import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ\s\-]+$")


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
# last_name, first_name, telefons, school, year, teacher, book, course, monthly_fee, balance
class Student(BaseModel):
    model_config = {"str_strip_whitespace": True}
    """Represents a student in the system.

    Attributes:
        id: Database primary key (auto-generated)
        active: Whether the student is currently active
        last_name: Student's last name (1-50 characters)
        first_name: Student's first name (1-50 characters)
        phone1: Primary phone number (required)
        phone2: Secondary phone number (optional)
        phone3: Tertiary phone number (optional)
        teacher: Teacher's name (required)
        book: Textbook information (optional)
        course: Course information (optional)
        school: School information (optional)
        year: Academic year (optional)
        monthly_fee: Monthly fee amount (> 0)
    """

    id: int | None = None
    active: bool = Field(default=True)
    last_name: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=50)
    phone1: str = Field(min_length=1, max_length=20)
    phone2: str = Field(default="", max_length=20)
    phone3: str = Field(default="", max_length=20)
    teacher: str = Field(min_length=1, max_length=20)
    book: str = Field(default="", max_length=50)
    course: str = Field(default="", max_length=20)
    school: str = Field(default="", max_length=20)
    year: str = Field(default="", max_length=20)
    monthly_fee: int = Field(ge=1, le=500000)

    @field_validator("last_name", "first_name", mode="before")
    def validate_names(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError("Nombre inválido")
        return v


class MovementType(str, Enum):
    FEE = "FEE"
    PAYMENT = "PAYMENT"
    REVERSED = "REVERSED"


class Movement(BaseModel):
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

    id: int | None = None
    student_id: int
    reference_id: int | None = None
    type: MovementType  # fee is <= 0, payment is >= 0 and reversed is stored or historical purposes
    amount: StrictInt = Field(
        ge=-500000, le=500000
    )  # Stored in pesos (no cents). 15000 = $15.000
    month: StrictInt = Field(ge=1, le=12)
    year: StrictInt = Field(ge=2000)
    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_sign(self):
        if self.type == MovementType.FEE and self.amount >= 0:
            raise ValueError("Fee must be negative")

        if self.type == MovementType.PAYMENT and self.amount <= 0:
            raise ValueError("Payment must be positive")

        if self.type == MovementType.REVERSED and not self.reference_id:
            raise ValueError("Reversal must have reference id")

        return self


@dataclass(frozen=True)
class DashboardMetrics:
    active_students: int
    expected_income: int
    collected: int
    total_debt: int
