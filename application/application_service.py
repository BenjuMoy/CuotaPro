import logging

from pydantic import ValidationError

from application.dto import CreatePaymentDTO, CreateStudentDTO, StudentDTO
from application.events import EventBus, RefreshType
from application.mappers import to_student_domain
from core.clock import Clock
from domain.accounting.values import Money, Period
from domain.shared.exceptions import BusinessRuleError
from domain.student.values import MonthlyFee
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
        student = to_student_domain(dto)

        with self.uow as uow:
            saved_student = uow.students.add(student)

        logger.info(
            "Student created | id=%s last_name=%s first_name=%s fee=%s",
            saved_student.id,
            saved_student.name.last_name,
            saved_student.name.first_name,
            saved_student.monthly_fee.amount,
        )

        self.event.notify(RefreshType.STUDENTS)
        return saved_student.id

    def update(self, dto: StudentDTO) -> int:
        student = to_student_domain(dto)

        with self.uow as uow:
            uow.students.update(student)

        logger.info(
            "Student updated | id=%s last_name=%s first_name=%s monthly_fee=%s",
            student.id,
            student.name.last_name,
            student.name.first_name,
            student.monthly_fee.amount,
        )

        self.event.notify(RefreshType.STUDENTS)
        return student.id


class AccountingService:
    def __init__(self, uow: UnitOfWork, events: EventBus, clock: Clock | None = None):
        self.uow = uow
        self.clock = clock or Clock()
        self.event = events

    def toggle_active(self, student_id: int) -> None:
        with self.uow as uow:
            account = uow.accounts.get(student_id)
            account.toggle_active()

            uow.students.update(account.student)

        self.event.notify(RefreshType.STUDENTS)
        logger.info("Student with id=%s switched state.", student_id)

    def add_payment(self, dto: CreatePaymentDTO) -> int:
        with self.uow as uow:
            account = uow.accounts.get(dto.student_id)

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
            accounts = uow.accounts.list_active_accounts()

            to_insert = []

            now = self.clock.now()

            for a in accounts:
                try:
                    movement = a.add_fee(
                        amount=Money(a.student.monthly_fee.amount),
                        period=period,
                        now=now,
                    )
                    to_insert.append(movement)

                except BusinessRuleError as e:
                    logger.debug("Skipping fee for student %s: %s", a.student.id, e)

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
            accounts = uow.accounts.list_active_accounts()

            affected = []
            for a in accounts:
                if a.student.monthly_fee.amount == old_fee:
                    a.change_monthly_fee(MonthlyFee(new_fee))
                    uow.students.update(a.student)
                    affected.append(a)

        count = len(affected)

        logger.info("Fees increased for %s students", count)
        self.event.notify(RefreshType.STUDENTS)

        return count

    def reverse(self, payment_id: int) -> int:
        with self.uow as uow:
            orig = uow.movements.get_by_id(payment_id)

            account = uow.accounts.get(orig.student_id)
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
