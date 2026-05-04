import logging
from functools import wraps
from typing import Callable

from pydantic import ValidationError

from application.dto import CreatePaymentDTO, CreateStudentDTO, StudentDTO
from application.events import EventBus, RefreshType
from application.mappers import to_student_domain
from core.clock import Clock
from domain.accounting.values import Money, Period
from domain.shared.exceptions import ApplicationError, BusinessRuleError
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


def handle_application_errors(func) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ValidationError as e:
            raise ApplicationError(handle_validation_error(e))
        except BusinessRuleError as e:
            raise ApplicationError(str(e))

    return wrapper


class StudentService:
    def __init__(self, uow: UnitOfWork, events: EventBus):
        self.uow = uow
        self.event = events

    @handle_application_errors
    def add(self, dto: CreateStudentDTO) -> int:
        student = to_student_domain(dto)

        with self.uow as uow:
            student_id = uow.students.add(student)

        logger.info(
            "Student created | id=%s last_name=%s first_name=%s fee=%s",
            student_id,
            dto.last_name,
            dto.first_name,
            dto.monthly_fee,
        )

        self.event.notify(RefreshType.STUDENTS)
        return student_id

    @handle_application_errors
    def update(self, dto: StudentDTO) -> int:
        s = to_student_domain(dto)

        with self.uow as uow:
            uow.students.update(s)

        logger.info(
            "Student updated | id=%s last_name=%s first_name=%s monthly_fee=%s",
            s.id,
            s.name.last_name,
            s.name.first_name,
            s.monthly_fee.amount,
        )

        self.event.notify(RefreshType.STUDENTS)
        return s.id


class AccountingService:
    def __init__(self, uow: UnitOfWork, events: EventBus, clock: Clock | None = None):
        self.uow = uow
        self.clock = clock or Clock()
        self.event = events

    @handle_application_errors
    def toggle_active(self, student_id: int) -> None:
        with self.uow as uow:
            account = uow.accounts.get(student_id)
            account.toggle_active()

            uow.students.update(account.student)

        self.event.notify(RefreshType.STUDENTS)
        logger.info("Student with id=%s switched state.", student_id)

    @handle_application_errors
    def add_payment(self, dto: CreatePaymentDTO) -> int:
        """
        Registers a payment for a student.

        Rules:
        - Payment must be positive
        - Student must have outstanding debt
        - Period cannot be in the future
        """
        with self.uow as uow:
            account = uow.accounts.get(dto.student_id)

            movement = account.add_payment(
                Money(dto.amount), Period(dto.month, dto.year), self.clock.now()
            )
            uow.accounts.save(account)

        logger.info(
            "Payment added | id=%s student_id=%s month=%s year=%s amount=%s",
            movement.id,
            movement.student_id,
            movement.period.month,
            movement.period.year,
            movement.amount.amount,
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return movement.id

    @handle_application_errors
    def add_fee(self, month: int, year: int) -> int:
        """
        Applies monthly fees to all active student accounts.

        Rules:
        - Only active students are considered
        - A fee is applied only if not already present for the period
        - Operation may partially succeed (best-effort)

        Returns:
            Number of students charged
        """
        period = Period(month, year)

        with self.uow as uow:
            accounts = uow.accounts.list_active_accounts()

            applied_count = 0

            now = self.clock.now()

            for a in accounts:
                if not a.can_apply_fee(period):
                    continue

                fee = a.add_fee(Money(a.student.monthly_fee.amount), period, now)

                uow.accounts.save(a)
                applied_count += 1

            if applied_count == 0:
                raise BusinessRuleError("No hay estudiantes para aplicar")

        logger.info(
            "Fees applied | period= %s/%s count= %s",
            period.month,
            period.year,
            applied_count,
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return applied_count

    @handle_application_errors
    def increase_monthly_fee(self, new_fee: int) -> int:
        with self.uow as uow:
            accounts = uow.accounts.list_active_accounts()
            count = 0
            for a in accounts:
                a.change_monthly_fee(MonthlyFee(new_fee))
                uow.accounts.save(a)
                count += 1

        logger.info("Fees increased for %s students", count)
        self.event.notify(RefreshType.STUDENTS)

        return count

    @handle_application_errors
    def reverse(self, payment_id: int) -> int:
        with self.uow as uow:
            orig = uow.movements.get_by_id(payment_id)

            account = uow.accounts.get(orig.student_id)
            movement = account.reverse(orig.id, self.clock.now())

            uow.accounts.save(account)

        logger.info(
            "Reversing movement entry | id=%s, period=%s/%s",
            movement.id,
            movement.period.month,
            movement.period.year,
        )

        self.event.notify(RefreshType.MOVEMENTS)
        return movement.id
