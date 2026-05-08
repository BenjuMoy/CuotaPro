from datetime import datetime

from pydantic import BaseModel, Field

from domain.shared.shared import MovementType

# --------------------------------------------------------------------------- #
# STUDENT
# --------------------------------------------------------------------------- #


class BaseStudentDTO(BaseModel):
    """Base model containing common student fields."""

    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)

    phone1: str
    phone2: str = ""
    phone3: str = ""

    teacher: str

    monthly_fee: int = Field(gt=0)


class CreateStudentDTO(BaseStudentDTO):
    """DTO for creating a new student with optional fields."""

    school: str = ""
    school_year: str = ""
    book: str = ""
    course: str = ""


class StudentDTO(BaseStudentDTO):
    """DTO for student representation with all required fields."""

    id: int
    active: bool

    school: str
    school_year: str
    book: str
    course: str


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
    amount: int
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)


# --------------------------------------------------------------------------- #
# STUDENT OVERVIEW (READ MODEL)
# --------------------------------------------------------------------------- #


class StudentOverview(BaseModel):
    student: StudentDTO
    balance: int
    movements: list[MovementDTO]
    last_payment: MovementDTO | None
