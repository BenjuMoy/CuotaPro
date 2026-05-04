from collections import defaultdict
from datetime import datetime

from domain.accounting.model import Movement
from domain.accounting.values import Money, Period
from domain.shared.exceptions import BusinessRuleError
from domain.shared.shared import MovementType, PeriodBalance
from domain.student.model import Student
from domain.student.values import MonthlyFee


class Account:
    """
    Aggregate root managing a student's financial state.

    Responsibilities:
    - Track all movements
    - Enforce accounting rules
    - Prevent invalid state transitions

    Invariants:
    - A movement can only be reversed once
    - A student with debt cannot be deactivated
    - Payments cannot be made if there is no debt
    """

    def __init__(self, student: Student, movements: list[Movement]):
        self.student = student  # entity inside aggregate
        self.movements = movements
        self._effective_cache: list[Movement] | None = None

    # --- Helpers --- #

    def _invalidate_cache(self):
        self._effective_cache = None

    # -------------------------
    # FACTORIES (validated)
    # -------------------------

    def add_payment(self, amount: Money, period: Period, now: datetime) -> Movement:
        self.ensure_active()

        if not self.balance.is_negative():
            raise BusinessRuleError("No hay deuda para el estudiante")

        m = Movement.create(
            student_id=self.student.id,
            type=MovementType.PAYMENT,
            amount=Money(abs(amount.amount)),
            period=period,
            reference_id=None,
            now=now,
        )

        self.movements.append(m)
        self._invalidate_cache()

        return m

    def add_fee(self, amount: Money, period: Period, now: datetime) -> Movement:
        if not self.can_apply_fee(period):
            raise BusinessRuleError("Fee already exists for this period")

        m = Movement.create(
            student_id=self.student.id,
            type=MovementType.FEE,
            amount=Money(-abs(amount.amount)),
            period=period,
            reference_id=None,
            now=now,
        )

        self.movements.append(m)
        self._invalidate_cache()

        return m

    def reverse(self, movement_id: int, now: datetime) -> Movement:
        original = next((m for m in self.movements if m.id == movement_id), None)

        if not original:
            raise BusinessRuleError("Movimiento no encontrado")

        original.ensure_reversible()

        if any(m.reference_id == original.id for m in self.movements):
            raise BusinessRuleError("Movimiento ya revertido")

        m = Movement.create(
            student_id=self.student.id,
            type=MovementType.REVERSED,
            amount=Money(-abs(original.amount.amount)),
            period=Period(now.month, now.year),
            reference_id=original.id,
            now=now,
        )
        m._validate(now)

        self.movements.append(m)
        self._invalidate_cache()

        return m

    # --- Commands --- #

    def toggle_active(self) -> None:
        if self.student.active and self.balance.is_negative():
            raise BusinessRuleError("No se puede desactivar estudiante con deuda")

        if self.student.active:
            self.student.deactivate()
        else:
            self.student.activate()

    # --- Properties --- #

    @property
    def balance(self) -> Money:
        total = Money(0)
        for m in self.effective():
            total += m.amount
        return total

    def has_fee(self, period: Period) -> bool:
        return any(
            m.period == period and m.type == MovementType.FEE for m in self.movements
        )

    def has_debt(self) -> bool:
        return self.balance.is_negative()

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

    def ensure_active(self):
        if not self.student.active:
            raise BusinessRuleError("Estudiante inactivo")

    def get_last_payment(self):
        for movement in reversed(self.effective()):
            if movement.type == MovementType.PAYMENT:
                return movement

    def change_monthly_fee(self, new_fee: MonthlyFee):
        if self.student.monthly_fee.amount == new_fee.amount:
            raise BusinessRuleError("Las cuotas no pueden ser iguales")

        if new_fee.amount < self.student.monthly_fee.amount:
            raise BusinessRuleError("La cuota nueva no puede ser menor que la vieja")

        self.student.monthly_fee = new_fee

    def can_apply_fee(self, period: Period) -> bool:
        return not self.has_fee(period)
