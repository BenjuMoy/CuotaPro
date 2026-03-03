from datetime import datetime
from sqlite3 import Connection

from app.models.exceptions import BusinessRuleError, NotFound
from app.models.models import Movement
from app.repositories.movement_repository import MovementRepository
from app.repositories.student_repository import StudentRepository


class AccountingService:
    def __init__(
        self,
        movement_repo: MovementRepository,
        student_repo: StudentRepository,
    ):
        self.movements = movement_repo
        self.students = student_repo

    def add_payment(
        self, student_id: int, month: int, year: int, amount: int
    ) -> Movement:
        """Adds payment to student by id. Amount comes always positive from ui and current year is assumed for payment."""

        if amount <= 0:
            raise BusinessRuleError("El pago debe ser positivo")

        now = datetime.now()
        if (year, month) > (now.year, now.month):
            raise BusinessRuleError("No se puede pagar un mes mas adelante que este")

        with self.movements.db_manager.transaction() as conn:
            if not self.students.get_by_id(student_id, conn):
                raise NotFound("Estudiante no encontrado")

            month_balance = self.movements.get_month_balance(
                student_id, month, year, conn
            )

            if month_balance >= 0:
                raise BusinessRuleError("No hay deuda para este periodo")

            movement = Movement(
                student_id=student_id,
                type="PAYMENT",
                amount=amount,
                month=month,
                year=year,
            )

            # Insert PAYMENT movement
            movement = self.movements.add(
                movement=movement,
                conn=conn,
            )

        return movement

    def add_fee(self, month: int, year: int) -> int:
        with self.movements.db_manager.transaction() as conn:
            valid_fee = self.movements.fees_not_applied_for_period(month, year, conn)

            if not valid_fee:
                raise BusinessRuleError("Cuotas ya aplicadas para este mes")

            students = self.students.get_all_active_students(conn)

            applied_count = 0
            for student in students:
                movement = Movement(
                    student_id=student.id,
                    type="FEE",
                    amount=-student.monthly_fee,
                    month=month,
                    year=year,
                )

                self.movements.add(movement, conn)
                applied_count += 1

            return applied_count

    def increase(self, old_monthly_fee: int, new_monthly_fee: int) -> int:
        if old_monthly_fee <= 0 or new_monthly_fee <= 0:
            raise BusinessRuleError("La cuota no puede ser negativa")

        if old_monthly_fee == new_monthly_fee:
            raise BusinessRuleError("Las cuotas no pueden ser iguales")

        if new_monthly_fee < old_monthly_fee:
            raise BusinessRuleError("La cuota nueva no puede ser menor que la vieja")

        with self.movements.db_manager.transaction() as conn:
            affected_students = self.students.increase_fees_for_amount(
                old_monthly_fee, new_monthly_fee, conn
            )

            if not affected_students:
                raise NotFound("No se encontraron alumnos con esa cuota")

        return affected_students

    def reverse(self, pago_id: int) -> Movement:
        """Reverses movement by id"""
        with self.movements.db_manager.transaction() as conn:
            orig = self.movements.get_by_id(pago_id, conn)

            # if not orig or not orig.id:
            #    raise NotFound("Movimiento no encontrado")

            if orig.type == "REVERSED":
                raise BusinessRuleError("No se puede revertir una reversión")

            if orig.type not in ("PAYMENT", "FEE"):
                raise BusinessRuleError("Movimiento no reversible")

            if orig.reference_id:
                raise BusinessRuleError("Movimiento ya revertido")

            self.movements.check_not_reversed(orig.id, conn)

            movement = Movement(
                student_id=orig.student_id,
                reference_id=orig.id,
                type="REVERSED",
                amount=-orig.amount,
                month=orig.month,
                year=orig.year,
            )
            movement = self.movements.add(movement, conn)
            return movement

    # Helpers

    def _get_month_balances(
        self, movements: list[Movement], student_id: int, conn: Connection
    ) -> dict[tuple[int, int], int]:
        """Genarates a dict that contains month and year as keys and debt in value"""
        passed_months = {}

        for movement in movements:
            if (movement.month, movement.year) not in passed_months:
                passed_months[movement.month, movement.year] = (
                    self.movements.get_month_balance(
                        student_id, movement.month, movement.year, conn
                    )
                )

        sorted_passed_months = dict(
            sorted(passed_months.items(), key=lambda x: (x[1], x[0]))
        )

        return sorted_passed_months

    # Getters

    def get_unpaid_months_with_debt(
        self, student_id: int
    ) -> dict[tuple[int, int], int]:
        with self.movements.db_manager.transaction() as conn:
            movements = self.movements.get_student_movements(student_id, conn)
            passed_months = self._get_month_balances(movements, student_id, conn)

        return {key: balance for key, balance in passed_months.items() if balance < 0}

    def get_all_movements(self) -> list[Movement]:
        with self.movements.db_manager.transaction() as conn:
            return self.movements.get_all(conn)

    def get_effective_payments(self) -> list[Movement]:
        with self.movements.db_manager.transaction() as conn:
            return self.movements.get_effective_payments(conn)

    def get_effective_fees(self) -> list[Movement]:
        with self.movements.db_manager.transaction() as conn:
            return self.movements.get_effective_fees(conn)

    def get_balance_by_id(self, student_id: int) -> int:
        with self.movements.db_manager.transaction() as conn:
            return self.movements.get_balance(student_id, conn)

    def get_last_fee_date(self) -> tuple[int, int] | None:
        """Returns a tuple containing the month and the year of the last applied fees."""
        with self.movements.db_manager.transaction() as conn:
            return self.movements.get_last_date_applied_fee(conn)

    def fees_not_applied_for_period(self) -> bool:
        now = datetime.now()
        month = now.month
        year = now.year
        with self.movements.db_manager.transaction() as conn:
            return self.movements.fees_not_applied_for_period(month, year, conn)

    # Wrappers

    def get_overview(self, student_id: int):
        with self.movements.db_manager.transaction() as conn:
            return {
                "student": self.students.get_by_id(student_id, conn),
                "balance": self.movements.get_balance(student_id, conn),
                "last_payment": self.movements.get_student_last_payment(
                    student_id, conn
                ),
                "movements": self.movements.get_effective_movements_by_id(
                    student_id, conn
                ),
            }
