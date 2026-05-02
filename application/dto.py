from datetime import datetime

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

    teacher: str

    school: str = ""
    school_year: str = ""
    book: str = ""
    course: str = ""

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
