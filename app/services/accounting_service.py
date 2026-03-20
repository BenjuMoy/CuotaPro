from datetime import datetime

from app.database.connection import DatabaseManager
from app.models.exceptions import BusinessRuleError, NotFound
from app.models.models import Movement, MovementType, Student, StudentOverview
from app.repositories.movement_repository import MovementRepository
from app.repositories.student_repository import StudentRepository


class AccountingService:
    def __init__(
        self,
        movement_repo: MovementRepository,
        student_repo: StudentRepository,
        db: DatabaseManager,
    ):
        self.movements = movement_repo
        self.students = student_repo
        self.db = db

    def add_payment(
        self, student_id: int, month: int, year: int, amount: int
    ) -> tuple[Student, int, Movement]:
        """Adds payment to student by id. Amount comes always positive from ui and current year is assumed for payment."""
        if amount <= 0:
            raise BusinessRuleError("El pago debe ser positivo")

        now = datetime.now()
        if (year, month) > (now.year, now.month):
            raise BusinessRuleError("No se puede pagar un mes mas adelante que este")

        with self.db.transaction() as conn:
            student = self.students.get_by_id(student_id, conn)

            if not student:
                raise NotFound("Estudiante no encontrado")

            if not student.active:
                raise NotFound("Estudiante inactivo")

            month_balance = self.movements.get_month_balance(
                student_id, month, year, conn
            )

            if month_balance >= 0:
                raise BusinessRuleError("No hay deuda para este periodo")

            movement = Movement(
                student_id=student_id,
                type=MovementType.PAYMENT,
                amount=amount,
                month=month,
                year=year,
            )

            # Insert PAYMENT movement
            movement = self.movements.add(
                movement=movement,
                conn=conn,
            )

            new_balance = self.movements.get_balance(student_id, conn)

        return student, new_balance, movement

    def add_fee(self, month: int, year: int) -> int:
        """Generate charges for all avtive students"""
        with self.db.transaction() as conn:
            students = self.students.get_students_without_fee(month, year, conn)

            if not students:
                raise NotFound("No ha estudiantes para aplicar")

            data = [
                (student.id, None, "FEE", -student.monthly_fee, month, year)
                for student in students
            ]

            self.movements.apply_fees(data, conn)

            return len(students)

    def increase_monthly_fee(self, old_monthly_fee: int, new_monthly_fee: int) -> int:
        """Increases the monthly fee."""
        if old_monthly_fee <= 0 or new_monthly_fee <= 0:
            raise BusinessRuleError("La cuota no puede ser negativa")

        if old_monthly_fee == new_monthly_fee:
            raise BusinessRuleError("Las cuotas no pueden ser iguales")

        if new_monthly_fee < old_monthly_fee:
            raise BusinessRuleError("La cuota nueva no puede ser menor que la vieja")

        with self.db.transaction() as conn:
            affected_students = self.students.increase_fees_for_amount(
                old_monthly_fee, new_monthly_fee, conn
            )

            if not affected_students:
                raise NotFound("No se encontraron alumnos con esa cuota")

        return affected_students

    def reverse(self, pago_id: int) -> Movement:
        """Reverses movement by id"""
        with self.db.transaction() as conn:
            orig = self.movements.get_by_id(pago_id, conn)

            # if not orig or not orig.id:
            #    raise NotFound("Movimiento no encontrado")

            if orig.type == MovementType.REVERSED:
                raise BusinessRuleError("No se puede revertir una reversión")

            if orig.type not in (MovementType.PAYMENT, MovementType.FEE):
                raise BusinessRuleError("Movimiento no reversible")

            if orig.reference_id:
                raise BusinessRuleError("Movimiento ya revertido")

            if self.movements.has_reversal(orig.id, conn):
                raise BusinessRuleError("Movimiento ya revertido")

            movement = Movement(
                student_id=orig.student_id,
                reference_id=orig.id,
                type=MovementType.REVERSED,
                amount=-orig.amount,
                month=orig.month,
                year=orig.year,
            )

            movement = self.movements.add(movement, conn)
            return movement

    # Getters

    def get_unpaid_months_with_debt(
        self, student_id: int
    ) -> list[tuple[int, int, int]]:
        with self.db.connect() as conn:
            passed_months = self.movements.get_general_month_balance(student_id, conn)

        return [month for month in passed_months if month[2] < 0]

    def get_all_movements(self) -> list[Movement]:
        with self.db.connect() as conn:
            return self.movements.get_all(conn)

    def get_effective_payments(self) -> list[Movement]:
        with self.db.connect() as conn:
            return self.movements.get_effective_payments(conn)

    def get_effective_fees(self) -> list[Movement]:
        with self.db.connect() as conn:
            return self.movements.get_effective_fees(conn)

    def get_balance_by_id(self, student_id: int) -> int:
        with self.db.connect() as conn:
            return self.movements.get_balance(student_id, conn)

    def get_last_fee_date(self) -> tuple[int, int] | None:
        """Returns a tuple containing the month and the year of the last applied fees."""
        with self.db.connect() as conn:
            return self.movements.get_last_date_applied_fee(conn)

    def get_students_without_fee(self, month: int, year: int) -> list[Student]:
        with self.db.connect() as conn:
            return self.students.get_students_without_fee(month, year, conn)

    def get_balances_for_students(self) -> dict[int, int]:
        with self.db.connect() as conn:
            return self.movements.get_balances_for_students(conn)

    def fees_not_applied_for_period(self) -> bool:
        now = datetime.now()
        month = now.month
        year = now.year
        with self.db.connect() as conn:
            return self.movements.fees_not_applied_for_period(month, year, conn)

    def get_total_collected_this_month(self, month: int, year: int):
        with self.db.connect() as conn:
            return self.movements.total_collected_this_month(month, year, conn)

    # Wrappers

    def get_overview(self, student_id: int) -> StudentOverview:
        with self.db.connect() as conn:
            return StudentOverview(
                student=self.students.get_by_id(student_id, conn),
                balance=self.movements.get_balance(student_id, conn),
                last_payment=self.movements.get_student_last_payment(student_id, conn),
                movements=self.movements.get_effective_movements_by_id(
                    student_id, conn
                ),
            )
