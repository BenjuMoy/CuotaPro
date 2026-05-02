from application.dto import CreateStudentDTO, MovementDTO, StudentDTO, StudentOverview
from domain.account.model import Account
from domain.accounting.model import Movement
from domain.student.model import Student
from domain.student.values import (
    Book,
    Course,
    MonthlyFee,
    PhoneNumber,
    SchoolYear,
    StudentName,
    Teacher,
)


def to_student_domain(dto: CreateStudentDTO | StudentDTO) -> Student:
    return Student(
        id=getattr(dto, "id", None),
        active=getattr(dto, "active", True),
        name=StudentName(dto.first_name, dto.last_name),
        phone1=PhoneNumber(dto.phone1),
        phone2=PhoneNumber(dto.phone2) if dto.phone2 else None,
        phone3=PhoneNumber(dto.phone3) if dto.phone3 else None,
        teacher=Teacher(dto.teacher),
        school=dto.school,
        school_year=SchoolYear(dto.school_year),
        book=Book(dto.book),
        course=Course(dto.course),
        monthly_fee=MonthlyFee(dto.monthly_fee),
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
        teacher=s.teacher.name,
        school=s.school if s.school else "",
        school_year=s.school_year.value if s.school_year else "",
        book=s.book.title if s.book else "",
        course=s.course.name if s.course else "",
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


def to_student_overview(account: Account) -> StudentOverview:
    return StudentOverview(
        student=to_student_dto(account.student),
        balance=account.balance.amount,
        movements=[to_movement_dto(m) for m in account.effective()],
    )
