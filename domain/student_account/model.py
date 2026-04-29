from collections import defaultdict

from domain.accounting.model import Movement, MovementType
from domain.accounting.values import Money, Period
from domain.shared.exceptions import AppValidationError, BusinessRuleError
from domain.shared.shared import PeriodBalance
from domain.student.model import Student


class StudentAccount:
    def __init__(self, student: Student, movements: list[Movement]):
        self.student = student
        self.movements = movements
        self._effective_cache: list[Movement] | None = None

    # --- Helpers --- #

    def _invalidate_cache(self):
        self._effective_cache = None

    # --- Commands --- #

    def add_payment(self, amount: Money, period: Period) -> Movement:
        if not self.balance.is_negative():
            raise AppValidationError("No hay deuda para el estudiante")

        movement = Movement.payment(self.student.id, amount, period)
        self.movements.append(movement)
        self._invalidate_cache()

        return movement

    def add_fee(self, amount: Money, period: Period) -> Movement:
        if self.has_fee(period):
            raise BusinessRuleError("Fee already exists for this period")

        movement = Movement.fee(self.student.id, amount, period)
        self.movements.append(movement)
        self._invalidate_cache()

        return movement

    def reverse(self, movement_id: int) -> Movement:
        original = next((m for m in self.movements if m.id == movement_id), None)

        if not original:
            raise AppValidationError("Movimiento no encontrado")

        original.ensure_reversible()

        if any(m.reference_id == original.id for m in self.movements):
            raise AppValidationError("Movimiento ya revertido")

        reversal = Movement.reversal(
            self.student.id, original.id, original.amount, original.period
        )

        self.movements.append(reversal)
        self._invalidate_cache()

        return reversal

    def toggle_active(self) -> None:
        if self.student.active and self.balance.is_negative():
            raise BusinessRuleError("No se puede desactivar estudiante con deuda")

        self.student.active = not self.student.active

    # --- Properties --- #

    @property
    def balance(self) -> Money:
        return Money(sum(m.amount.amount for m in self.effective()))

    def has_fee(self, period: Period) -> bool:
        return any(
            m.period == period and m.type == MovementType.FEE for m in self.movements
        )

    def has_debt(self) -> bool:
        return self.balance.amount < 0

    def effective(self) -> list[Movement]:
        if self._effective_cache is None:
            reversed_ids = {m.reference_id for m in self.movements if m.reference_id}
            self._effective_cache = [
                m
                for m in self.movements
                if m.id not in reversed_ids and m.reference_id is None
            ]
        return self._effective_cache

    def balance_by_period(self) -> list[PeriodBalance]:
        """Returns [(month, year, balance)] using effective movements."""
        buckets = defaultdict(int)

        for m in self.effective():
            key = (m.period.month, m.period.year)
            buckets[key] += m.amount.amount

        return [(PeriodBalance(m, y, total)) for (m, y), total in buckets.items()]

    def unpaid_periods(self) -> list[PeriodBalance]:
        return [p for p in self.balance_by_period() if p.amount < 0]

    def total_paid_in_period(self, period: Period) -> int:
        return sum(
            m.amount.amount
            for m in self.effective()
            if m.type == MovementType.PAYMENT and m.period == period
        )
