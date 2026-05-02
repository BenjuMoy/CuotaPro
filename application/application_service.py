import logging
from collections import defaultdict

from pydantic import ValidationError

from application.dto import CreatePaymentDTO, CreateStudentDTO, StudentDTO
from application.events import EventBus, RefreshType
from application.mappers import to_student_domain
from core.clock import Clock
from domain.accounting.values import Money, Period
from domain.shared.exceptions import BusinessRuleError
from domain.student.values import MonthlyFee
from domain.student_account.model import StudentAccount
from infrastructure.database.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


def handle_validation_error(e: ValidationError):
    error_messages = []
    for error in e.errors():
        field = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]
        error_messages.append(f"Campo '{field}': {msg}")
    return "\n".join(error_messages)


class StudentService:
    def __init__(self, uow: UnitOfWork, events: EventBus):
        self.uow = uow
        self.event = events

    def add(self, dto: CreateStudentDTO) -> int:
        new_student = to_student_domain(dto)

        with self.uow as uow:
            saved_student = uow.students.add(new_student)

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

        with self.uow as uow:
            uow.students.update(updated_student)

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
    def __init__(self, uow: UnitOfWork, events: EventBus, clock: Clock | None = None):
        self.uow = uow
        self.clock = clock or Clock()
        self.event = events

    def _build_account(self, student_id: int, uow: UnitOfWork) -> StudentAccount:
        student = uow.students.get_by_id(student_id)
        movements = uow.movements.list_by_student_id(student_id)
        return StudentAccount(student, movements)

    def toggle_active(self, student_id: int) -> None:
        with self.uow as uow:
            account = self._build_account(student_id, uow)
            account.toggle_active()

            uow.students.update(account.student)

        self.event.notify(RefreshType.STUDENTS)
        logger.info("Student with id=%s switched state.", student_id)

    def add_payment(self, dto: CreatePaymentDTO) -> int:
        with self.uow as uow:
            account = self._build_account(dto.student_id, uow)

            movement = account.add_payment(
                Money(dto.amount), Period(dto.month, dto.year), self.clock.now()
            )

            uow.movements.add(movement)

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

        with self.uow as uow:
            students = uow.students.list_active()
            student_ids = [s.id for s in students]

            movements = uow.movements.list_by_students_ids(student_ids)

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
                        now=self.clock.now(),
                    )

                    to_insert.append(movement)
                except BusinessRuleError as e:
                    logger.debug("Skipping fee for student %s: %s", s.id, e)
                    continue

            if not to_insert:
                raise BusinessRuleError("No hay estudiantes para aplicar")

            uow.movements.add_many(to_insert)

        logger.info(
            "Fees applied | period= %s/%s count= %s",
            period.month,
            period.year,
            len(to_insert),
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return len(to_insert)

    def increase_monthly_fee(self, old_fee: int, new_fee: int) -> int:
        with self.uow as uow:
            students = uow.students.list_active()

            affected = []

            for s in students:
                if s.monthly_fee.amount == old_fee:
                    s.change_monthly_fee(MonthlyFee(new_fee))
                    uow.students.update(s)
                    affected.append(s)

        count = len(affected)

        logger.info("Fees increased for %s students", count)
        self.event.notify(RefreshType.STUDENTS)

        return count

    def reverse(self, payment_id: int) -> int:
        with self.uow as uow:
            orig = uow.movements.get_by_id(payment_id)

            account = self._build_account(orig.student_id, uow)
            reversed_movement = account.reverse(orig.id, self.clock.now())

            movement = uow.movements.add(reversed_movement)

        logger.info(
            "Reversing movement entry | id=%s, period=%s/%s",
            movement.id,
            movement.period.month,
            movement.period.year,
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return movement.id
