from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from domain.accounting.model import MovementType

# --------------------------------------------------------------------------- #
# STUDENT
# --------------------------------------------------------------------------- #


class CreateStudentDTO(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)

    phone1: str
    phone2: str = ""
    phone3: str = ""

    teacher: Literal["Asuncion", "Daniela", "Florencia", "Kiana", "Romina", "Silvia"]

    school: str = ""
    school_year: Literal[
        "",
        "Kindergarden",
        "1 EP",
        "2 EP",
        "3 EP",
        "4 EP",
        "5 EP",
        "6 EP",
        "1 ES",
        "2 ES",
        "3 ES",
        "4 ES",
        "5 ES",
        "6 ES",
    ] = ""
    book: Literal[
        "",
        "Power Up Start P. 1",
        "Power Up Start P. 2",
        "Learn With Us 1",
        "Power Up 1",
        "Power Up 2",
        "Own It 1",
        "Gateway A1",
        "Gateway A2",
        "Gateway B1",
        "Gateway B2",
        "Gold. Exp. FCE",
        "Gold. Exp. CAE",
        "Insight Elem.",
        "Insight Pre. Int.",
        "Insight Int.",
    ] = ""
    course: Literal[
        "",
        "Kids 1",
        "Kids 2",
        "Kids 3",
        "Junior 1",
        "Junior 2",
        "Junior 3",
        "Senior 1",
        "Senior 2",
        "Senior 3",
        "Senior 4",
        "Senior 5",
        "Senior 6",
        "Adults 1",
        "Adults 2",
        "Adults 3",
        "Adults 4",
    ] = ""

    monthly_fee: int = Field(gt=0)


class StudentDTO(BaseModel):
    id: int
    active: bool

    first_name: str
    last_name: str

    phone1: str
    phone2: str = ""
    phone3: str = ""

    teacher: str
    school: str
    school_year: str
    book: str
    course: str

    monthly_fee: int


# --------------------------------------------------------------------------- #
# MOVEMENTS
# --------------------------------------------------------------------------- #


class MovementDTO(BaseModel):
    id: int
    student_id: int

    type: MovementType
    amount: int

    month: int
    year: int

    reference_id: int | None
    created_at: datetime


# --------------------------------------------------------------------------- #
# PAYMENTS
# --------------------------------------------------------------------------- #


class CreatePaymentDTO(BaseModel):
    student_id: int
    amount: int = Field(gt=0, description="EL monto del pago debe ser positivo")
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)


# --------------------------------------------------------------------------- #
# STUDENT OVERVIEW (READ MODEL)
# --------------------------------------------------------------------------- #


class StudentOverview(BaseModel):
    student: StudentDTO
    balance: int
    movements: list[MovementDTO]
