import logging
from datetime import datetime
from pathlib import Path
from sqlite3 import IntegrityError
from typing import Any, Callable

from pydantic import ValidationError

from app.models.exceptions import (
    AppValidationError,
    BusinessRuleError,
    ConflictError,
    NotFound,
)
from app.models.models import (
    Movement,
    Student,
)
from app.services.service_container import ServiceContainer


class ApplicationService:
    """
    Central controller for the application using SQLite database.
    Manages state and coordinates between the data layer and the UI.
    """

    def __init__(self, services: ServiceContainer):
        self.services = services

        self.logger = logging.getLogger(__name__)
        self._subscribers: list[Callable[[], None]] = []

    # --- Subscription Pattern for UI Updates ---
    def subscribe(self, callback: Callable[[], None]) -> None:
        """Allows a UI component to subscribe to data changes."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify_subscribers(self) -> None:
        """Notifies all subscribed components that data has changed."""
        for callback in list(self._subscribers):
            try:
                callback()
            except Exception as e:
                self.logger.exception(f"Subscriber error: {e}")
                # logging.exception(f"Subscriber error {e}")

    # --- Centralized Error Handling ---
    @staticmethod
    def _handle_validation_error(e: ValidationError):
        """Converts Pydantic AppValidationError into a custom ErrorDeValidacion."""
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            error_messages.append(f"Campo '{field}': {msg}")
        return "\n".join(error_messages)

    # ======================
    # Students
    # ======================

    def add_student(self, data: dict) -> Student:
        """Adds a student to the database."""
        try:
            saved_student = self.services.student.add(data)

            self.logger.info(
                "Student created | id=%s last_name=%s first_name=%s fee=%s",
                saved_student.id,
                saved_student.last_name,
                saved_student.first_name,
                saved_student.monthly_fee,
            )

            self._notify_subscribers()
            return saved_student

        except ValidationError as e:
            formatted = self._handle_validation_error(e)
            raise AppValidationError(formatted) from e

        except IntegrityError as e:
            raise ConflictError("El estudiante ya existe") from e

    def update_student(self, student_id: int, data: dict[str, Any]) -> Student | None:
        """Updates a student, updates state, and saves."""
        try:
            updated_student = self.services.student.update(student_id, data)

            self.logger.info(
                "Student updated | id=%s last_name=%s first_name=%s monthly_fee=%s",
                updated_student.id,
                updated_student.last_name,
                updated_student.first_name,
                updated_student.monthly_fee,
            )
            self._notify_subscribers()
            return updated_student

        except ValidationError as e:
            formatted = self._handle_validation_error(e)
            raise AppValidationError(formatted) from e

        except IntegrityError as e:
            raise ConflictError("Conflicto de datos") from e

    def switch_student_state(self, student_id: int) -> Student | None:
        """Handles the state switch."""
        try:
            updated_student = self.services.student.switch_state(student_id)

            self.logger.info("Student with id=%s switched state.", updated_student.id)
            self._notify_subscribers()
            return updated_student

        except NotFound:
            raise

    # Student getters

    def get_all_students(self) -> list[Student]:
        """Get all students from db."""
        return self.services.student.get_all()

    def get_all_active_students(self) -> list[Student]:
        return self.services.student.get_all_active()

    def get_student_by_id(self, student_id: int) -> Student:
        """Retrieves a single student by their ID."""
        return self.services.student.get_by_id(student_id)

    def get_students_debtors(self) -> list[Student]:
        """Search students by debt."""
        return self.services.student.get_debtors()

    def search_student_by_name(self, name: str) -> list[Student]:
        """Search students by name."""
        return self.services.student.search_by_name(name)

    def search_student_by_teacher(self, teacher_name: str) -> list[Student]:
        """Search students by teacher name."""
        return self.services.student.search_by_teacher(teacher_name)

    def count_students_by_monthly_fee(self, monthly_fee: int) -> int:
        """Search students by monthly_fee."""
        return self.services.student.count_by_monthly_fee(monthly_fee)

    def get_active_student_count(self) -> int:
        return self.services.student.get_active_count()

    # ======================
    # Accounting
    # ======================

    def add_payment_to_student(
        self, student_id: int, month: int, year: int, amount: int
    ) -> dict[str, Student | int | Movement]:
        """Adds payment to student by id. Amount comes always positive from ui and current year is assumed for payment."""
        student, new_balance, movement = self.services.accounting.add_payment(
            student_id, month, year, amount
        )

        self.logger.info(
            "Payment added | student_id=%s month=%s year=%s amount=%s new_balance=%s",
            movement.student_id,
            movement.month,
            movement.year,
            movement.amount,
            new_balance,
        )
        self._notify_subscribers()

        return {
            "student": student,
            "balance": new_balance,
            "last_payment": movement,
        }

    # Payment getters

    def get_all_movements(self) -> list[Movement]:
        return self.services.accounting.get_all_movements()

    def get_effective_payments(self) -> list[Movement]:
        return self.services.accounting.get_effective_payments()

    def get_effective_fees(self) -> list[Movement]:
        return self.services.accounting.get_effective_fees()

    def get_balance_by_id(self, student_id: int) -> int:
        return self.services.accounting.get_balance_by_id(student_id)

    def get_unpaid_months_by_student_id(
        self, student_id: int
    ) -> list[tuple[int, int, int]]:
        return self.services.accounting.get_unpaid_months_with_debt(student_id)

    def get_fees_list(self) -> list[tuple[int, int]]:
        return self.services.student.get_fees_list()

    def get_last_applied_fees_date(self) -> tuple[int, int] | None:
        """Returns a tuple containing the month and the year of the last applied fees."""
        return self.services.accounting.get_last_fee_date()

    def fees_not_applied_for_period(self) -> bool:
        return self.services.accounting.fees_not_applied_for_period()

    # --- Administrative actions --- #

    def apply_monthly_fees(self) -> int:
        """Generates charges for all active students"""
        now = datetime.now()
        month = now.month
        year = now.year

        applied_count = self.services.accounting.add_fee(month, year)

        self.logger.info(
            "Monthly fees applied | month=%s year=%s students=%s",
            month,
            year,
            applied_count,
        )
        self._notify_subscribers()
        return applied_count

    def increase_fee_amount(self, old_monthly_fee: int, new_monthly_fee: int) -> int:
        """Increase fees for all students with a specific fee amount."""
        affected_students = self.services.accounting.increase_monthly_fee(
            old_monthly_fee, new_monthly_fee
        )

        self.logger.info("Fees increased for %s students", affected_students)
        self._notify_subscribers()
        return affected_students

    def reverse_movement(self, pago_id: int) -> None:
        """Reverses movement by id"""
        try:
            movement = self.services.accounting.reverse(pago_id)

            self.logger.info(
                "Reversing movement entry | id=%s, month=%s year=%s",
                movement.id,
                movement.month,
                movement.year,
            )
            self._notify_subscribers()

        except BusinessRuleError:
            raise

        except NotFound:
            raise

    # Wrappers

    def get_student_payment_overview(self, student_id: int) -> dict:
        return self.services.accounting.get_overview(student_id)

    # --- Informes ---

    def get_salary_report(self, professor_name: str):
        """
        Calculates the total payment for a specific professor based on active student fees.

        Returns:
            dict: {
                'professor': str,
                'total': int,
                'student_count': int,
                'details': list[dict]  # Each dict contains student name and fee
            }

        Raises:
            ValueError: If professor is not found or has no students.
        """
        return self.services.student.get_salary(professor_name)

    # -------- Maintenance --------

    def create_backup(self):
        return self.services.maintenance.create_backup()

    def restore_backup(self, file_path: str):
        return self.services.maintenance.restore_backup(file_path)

    def list_backup_files(self) -> list[Path]:
        return self.services.maintenance.list_backup_files()

    def verify_integrity(self):
        return self.services.maintenance.verify_integrity()

    def export_to_csv(self):
        return self.services.maintenance.export_to_csv()

    def get_database_stats(self):
        return self.services.maintenance.get_database_stats()
