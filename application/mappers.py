from application.dto import (
    CreatePaymentDTO,
    CreateStudentDTO,
    MovementDTO,
    StudentDTO,
    StudentOverview,
)
from domain.accounting.model import Movement, MovementType
from domain.accounting.values import Money, Period
from domain.student.model import Student
from domain.student.values import MonthlyFee, PhoneNumber, StudentName
from domain.student_account.model import StudentAccount


def to_student_domain(dto: CreateStudentDTO | StudentDTO) -> Student:
    return Student(
        id=getattr(dto, "id", None),
        active=getattr(dto, "active", True),
        name=StudentName(dto.first_name, dto.last_name),
        phone1=PhoneNumber(dto.phone1),
        phone2=PhoneNumber(dto.phone2) if dto.phone2 else None,
        phone3=PhoneNumber(dto.phone3) if dto.phone3 else None,
        teacher=dto.teacher,
        school=dto.school,
        school_year=dto.school_year,
        book=dto.book,
        course=dto.course,
        monthly_fee=MonthlyFee(dto.monthly_fee),
    )


def to_payment_domain(dto: CreatePaymentDTO) -> Movement:
    return Movement(
        student_id=dto.student_id,
        movement_type=MovementType.PAYMENT,
        amount=Money(dto.amount),
        period=Period(dto.month, dto.year),
    )


def to_student_dto(s: Student) -> StudentDTO:
    return StudentDTO(
        id=s.id,
        active=s.active,
        first_name=s.name.first_name,
        last_name=s.name.last_name,
        phone1=s.phone1.value,
        phone2=s.phone2.value if s.phone2 else "",
        phone3=s.phone3.value if s.phone3 else "",
        teacher=s.teacher,
        school=s.school,
        school_year=s.school_year,
        book=s.book,
        course=s.course,
        monthly_fee=s.monthly_fee.amount,
    )


def to_movement_dto(m: Movement) -> MovementDTO:
    return MovementDTO(
        id=m.id,
        student_id=m.student_id,
        type=m.type,
        amount=m.amount.amount,
        month=m.period.month,
        year=m.period.year,
        reference_id=m.reference_id,
        created_at=m.created_at,
    )


def to_student_overview(account: StudentAccount) -> StudentOverview:
    return StudentOverview(
        student=to_student_dto(account.student),
        balance=account.balance.amount,
        movements=[to_movement_dto(m) for m in account.effective()],
    )
