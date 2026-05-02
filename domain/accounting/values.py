from dataclasses import dataclass
from datetime import datetime

from domain.shared.exceptions import AppValidationError, BusinessRuleError

MAX_AMOUNT = 5_000_000


@dataclass(frozen=True)
class Money:
    amount: int

    def __post_init__(self):
        if not (-MAX_AMOUNT <= self.amount <= MAX_AMOUNT):
            raise AppValidationError("Invalid amount")

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __neg__(self) -> "Money":
        return Money(-self.amount)

    def is_positive(self) -> bool:
        return self.amount > 0

    def is_negative(self) -> bool:
        return self.amount < 0

    def debit(self, amount: int) -> "Money":
        """Subtract the specified amount from this Money instance."""
        return Money(self.amount - amount)

    def credit(self, amount: int) -> "Money":
        """Add the specified amount to this Money instance."""
        return Money(self.amount + amount)


@dataclass(frozen=True)
class Period:
    month: int
    year: int

    def __post_init__(self):
        if not (1 <= self.month <= 12):
            raise AppValidationError("Invalid month")
        if self.year < 2000:
            raise AppValidationError("Invalid year")

    def ensure_not_future(self, now: datetime):
        if (self.year, self.month) > (now.year, now.month):
            raise BusinessRuleError("No se puede pagar un mes mas adelante que este")
