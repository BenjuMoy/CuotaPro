import logging
from collections import defaultdict

from pydantic import ValidationError

from application.dto import CreatePaymentDTO, CreateStudentDTO, StudentDTO
from application.events import EventBus, RefreshType
from application.mappers import to_payment_domain, to_student_domain
from core.clock import Clock
from domain.accounting.model import Movement
from domain.accounting.repository import MovementRepository
from domain.accounting.values import Money, Period
from domain.shared.exceptions import BusinessRuleError
from domain.student.repository import StudentRepository
from domain.student.values import MonthlyFee
from domain.student_account.model import StudentAccount
from infrastructure.database.unit_of_work import UnitOfWork

# TODO Commands return metadata or results instead of objects?

logger = logging.getLogger(__name__)


def handle_validation_error(e: ValidationError):
    error_messages = []
    for error in e.errors():
        field = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]
        error_messages.append(f"Campo '{field}': {msg}")
    return "\n".join(error_messages)


class StudentService:
    def __init__(
        self, uow: UnitOfWork, events: EventBus, student_repo: StudentRepository
    ):
        self.uow = uow
        self.repo = student_repo
        self.event = events

    def add(self, dto: CreateStudentDTO) -> int:
        new_student = to_student_domain(dto)

        with self.uow:
            saved_student = self.repo.add(new_student)

        logger.info(
            "Student created | id=%s last_name=%s first_name=%s fee=%s",
            saved_student.id,
            saved_student.name.last_name,
            saved_student.name.first_name,
            saved_student.monthly_fee,
        )

        self.event.notify(RefreshType.STUDENTS)
        return saved_student.id

    def update(self, dto: StudentDTO) -> int:
        updated_student = to_student_domain(dto)

        with self.uow:
            self.repo.update(updated_student)

        logger.info(
            "Student updated | id=%s last_name=%s first_name=%s monthly_fee=%s",
            updated_student.id,
            updated_student.name.last_name,
            updated_student.name.first_name,
            updated_student.monthly_fee,
        )

        self.event.notify(RefreshType.STUDENTS)
        return updated_student.id


class AccountingService:
    def __init__(
        self,
        uow: UnitOfWork,
        events: EventBus,
        student_repo: StudentRepository,
        movement_repo: MovementRepository,
        clock: Clock | None = None,
    ):
        self.uow = uow
        self.clock = clock or Clock()
        self.event = events
        self.movements = movement_repo
        self.students = student_repo

    def _build_account(self, student_id: int) -> StudentAccount:
        student = self.students.get_by_id(student_id)
        movements = self.movements.list_by_student_id(student_id)
        return StudentAccount(student, movements)

    def toggle_active(self, student_id: int) -> None:
        with self.uow:
            account = self._build_account(student_id)
            account.toggle_active()

            self.students.update(account.student)

        self.event.notify(RefreshType.STUDENTS)
        logger.info("Student with id=%s switched state.", student_id)

    def add_payment(self, dto: CreatePaymentDTO) -> int:
        movement = to_payment_domain(dto)

        with self.uow:
            account = self._build_account(dto.student_id)
            account.student.ensure_active()

            movement = account.add_payment(movement.amount, movement.period)

            self.movements.add(movement)

        logger.info(
            "Payment added | student_id=%s month=%s year=%s amount=%s",
            movement.student_id,
            movement.period.month,
            movement.period.year,
            movement.amount.amount,
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return movement.id

    def add_fee(self, month: int, year: int) -> int:
        period = Period(month, year)

        with self.uow:
            students = self.students.list_active()
            student_ids = [s.id for s in students if s.id]

            movements = self.movements.list_by_students_ids(student_ids)

            movements_by_student = defaultdict(list)
            for m in movements:
                movements_by_student[m.student_id].append(m)

            to_insert = []

            for s in students:
                account = StudentAccount(s, movements_by_student.get(s.id, []))

                try:
                    movement = account.add_fee(
                        amount=Money(s.monthly_fee.amount),
                        period=period,
                    )

                    to_insert.append(movement)
                except BusinessRuleError as e:
                    logger.debug("Skipping fee for student %s: %s", s.id, e)
                    continue

            if not to_insert:
                raise BusinessRuleError("No hay estudiantes para aplicar")

            self.movements.add_many(to_insert)

        logger.info(
            "Fees applied | period= %s/%s count= %s",
            period.month,
            period.year,
            len(to_insert),
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return len(to_insert)

    def increase_monthly_fee(self, old_fee: int, new_fee: int) -> int:
        with self.uow:
            students = self.students.list_active()

            affected = []

            for s in students:
                if s.monthly_fee.amount == old_fee:
                    s.change_monthly_fee(MonthlyFee(new_fee))
                    self.students.update(s)
                    affected.append(s)

        count = len(affected)

        logger.info("Fees increased for %s students", count)
        self.event.notify(RefreshType.STUDENTS)

        return count

    def reverse(self, payment_id: int) -> int:
        with self.uow:
            orig = self.movements.get_by_id(payment_id)

            account = self._build_account(orig.student_id)
            reversed_movement = account.reverse(orig.id)

            movement = self.movements.add(reversed_movement)

        logger.info(
            "Reversing movement entry | id=%s, period=%s/%s",
            movement.id,
            movement.period.month,
            movement.period.year,
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return movement.id
