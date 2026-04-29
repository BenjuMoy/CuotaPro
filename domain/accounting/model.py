from datetime import datetime
from enum import Enum

from core.clock import Clock
from domain.accounting.values import Money, Period
from domain.shared.exceptions import BusinessRuleError


#  NOTE Should i move to shared/?
class MovementType(str, Enum):
    FEE = "FEE"
    PAYMENT = "PAYMENT"
    REVERSED = "REVERSED"


class Movement:
    """Represents a movement in the system.

    Attributes:
        id: Database primary key (auto-generated)
        stdent_id: Database foreign key pointing to the student
        type: type of transaction:
            FEE -> Negative amount
            PAYMENT -> Positive amount
            REVERSED -> Negative of original
        amount: sum of money, eg. 15000 = $15.000 (no cents)
        month: month of the applied transaction (1 - 12)
        year: year of the transaction (>= 2000)
        reference_id: Original movement id
        created_at: datetime
    """

    def __init__(
        self,
        student_id: int,
        movement_type: MovementType,
        amount: Money,
        period: Period,
        reference_id: int | None = None,
        created_at: datetime | None = None,
        id: int | None = None,
        clock: Clock | None = None,
    ):
        self.id = id
        self.student_id = student_id
        self.type = movement_type  # fee is <= 0, payment is >= 0 and reversed is stored or historical purposes
        self.amount = amount  # Stored in pesos (no cents). 15000 = $15.000
        self.period = period
        self.reference_id = reference_id
        self.created_at = created_at or Clock().now()
        self.clock = clock or Clock()

        self._validate()

    def _validate(self):
        if self.type == MovementType.FEE and self.amount.is_positive():
            raise BusinessRuleError("Fee must be negative")

        if self.type == MovementType.PAYMENT and self.amount.is_negative():
            raise BusinessRuleError("Payment must be positive")

        if self.type == MovementType.REVERSED and not self.reference_id:
            raise BusinessRuleError("Reversal must have reference id")

        self.period.ensure_not_future(self.clock)

    @classmethod
    def fee(cls, student_id: int, amount: Money, period: Period):
        return cls(
            student_id=student_id,
            movement_type=MovementType.FEE,
            amount=Money(-abs(amount.amount)),
            period=period,
        )

    @classmethod
    def payment(cls, student_id: int, amount: Money, period: Period):
        return cls(
            student_id=student_id,
            movement_type=MovementType.PAYMENT,
            amount=amount,
            period=period,
        )

    @classmethod
    def reversal(cls, student_id: int, original_id: int, amount: Money, period: Period):
        return cls(
            student_id=student_id,
            reference_id=original_id,
            movement_type=MovementType.REVERSED,
            amount=Money(-abs(amount.amount)),
            period=period,
        )

    def ensure_reversible(self):
        if self.type == MovementType.REVERSED:
            raise BusinessRuleError("No se puede revertir una reversión")

        if self.type not in (MovementType.PAYMENT, MovementType.FEE):
            raise BusinessRuleError("Movimiento no reversible")

        if self.reference_id is not None:
            raise BusinessRuleError("No se puede revertir una reversion")

        # if not orig or not orig.id:
        #    raise NotFound("Movimiento no encontrado")
