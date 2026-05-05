from datetime import datetime

from domain.accounting.values import Money, Period
from domain.shared.exceptions import BusinessRuleError
from domain.shared.shared import MovementType

# TODO change name to AccountMovement?


class Movement:
    """
    Represents a financial movement affecting a student's account.

    Invariants:
    - FEE movements must have negative amounts
    - PAYMENT movements must have positive amounts
    - REVERSED movements must reference an existing movement
    - Period cannot be in the future
    """

    def __init__(
        self,
        *,
        id: int | None,
        student_id: int,
        type: MovementType,
        amount: Money,
        period: Period,
        reference_id: int | None,
        created_at: datetime,
    ):
        self.id = id
        self.student_id = student_id
        self.type = type  # fee is <= 0, payment is >= 0 and reversed is stored or historical purposes
        self.amount = amount  # Stored in pesos (no cents). 15000 = $15.000
        self.period = period
        self.reference_id = reference_id
        self.created_at = created_at

    # -------------------------
    # GENERIC FACTORY (validated)
    # -------------------------

    @classmethod
    def create(
        cls,
        student_id: int,
        type: MovementType,
        amount: Money,
        period: Period,
        reference_id: int | None,
        now: datetime,
    ):
        obj = cls(
            id=None,
            student_id=student_id,
            type=type,
            amount=amount,
            period=period,
            reference_id=reference_id,
            created_at=now,
        )
        obj._validate(now)
        return obj

    # -------------------------
    # REHYDRATION (NO validation)
    # -------------------------

    @classmethod
    def from_persistence(
        cls,
        *,
        id: int,
        student_id: int,
        type: MovementType,
        amount: Money,
        period: Period,
        reference_id: int | None,
        created_at: datetime,
    ):
        obj = cls.__new__(cls)

        obj.id = id
        obj.student_id = student_id
        obj.type = type
        obj.amount = amount
        obj.period = period
        obj.reference_id = reference_id
        obj.created_at = created_at

        return obj

    # -------------------------
    # VALIDATION
    # -------------------------

    def _validate(self, now: datetime) -> None:
        if self.type == MovementType.FEE and self.amount.is_positive():
            raise BusinessRuleError("Fee must be negative")

        if self.type == MovementType.PAYMENT and self.amount.is_negative():
            raise BusinessRuleError("Payment must be positive")

        if self.type == MovementType.REVERSED and not self.reference_id:
            raise BusinessRuleError("Reversal must have reference id")

        self.period.ensure_not_future(now)

    def ensure_reversible(self) -> None:
        if self.type == MovementType.REVERSED:
            raise BusinessRuleError("No se puede revertir una reversión")

        if self.type not in (MovementType.PAYMENT, MovementType.FEE):
            raise BusinessRuleError("Movimiento no reversible")

        if self.reference_id is not None:
            raise BusinessRuleError("No se puede revertir una reversion")

        # if not orig or not orig.id:
        #    raise NotFound("Movimiento no encontrado")
