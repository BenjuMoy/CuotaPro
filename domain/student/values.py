import re
from dataclasses import dataclass

from domain.shared.exceptions import AppValidationError

NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ\s\-]+$")


@dataclass(frozen=True)
class StudentName:
    first_name: str
    last_name: str

    def __post_init__(self):
        if not (1 <= len(self.first_name) <= 50):
            raise AppValidationError("Invalid first name length")
        if not (1 <= len(self.last_name) <= 50):
            raise AppValidationError("Invalid last name length")
        if not NAME_PATTERN.match(self.first_name):
            raise AppValidationError("Invalid first name")
        if not NAME_PATTERN.match(self.last_name):
            raise AppValidationError("Invalid last name")


@dataclass(frozen=True)
class PhoneNumber:
    value: str

    def __post_init__(self):
        if not (1 <= len(self.value) <= 20):
            raise AppValidationError("Invalid phone number")


@dataclass(frozen=True)
class MonthlyFee:
    amount: int

    def __post_init__(self):
        if not (1 <= self.amount <= 500000):
            raise AppValidationError("Invalid monthly fee")
