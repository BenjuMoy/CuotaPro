from application.dto import CreateStudentDTO, MovementDTO, StudentDTO, StudentOverview
from domain.account.model import Account
from domain.accounting.model import Movement
from domain.student.model import StudentProfile
from domain.student.values import (
    Book,
    Course,
    MonthlyFee,
    PhoneNumber,
    SchoolYear,
    StudentName,
    Teacher,
)


def to_student_domain(dto: CreateStudentDTO | StudentDTO) -> StudentProfile:
    return StudentProfile(
        id=getattr(dto, "id", None),
        active=getattr(dto, "active", True),
        name=StudentName(dto.first_name, dto.last_name),
        phone1=PhoneNumber(dto.phone1),
        phone2=PhoneNumber.optional(dto.phone2),
        phone3=PhoneNumber.optional(dto.phone3),
        teacher=Teacher(dto.teacher),
        school=dto.school,
        school_year=SchoolYear(dto.school_year) if dto.school_year else None,
        book=Book(dto.book) if dto.book else None,
        course=Course(dto.course) if dto.course else None,
        monthly_fee=MonthlyFee(dto.monthly_fee),
    )


def to_student_dto(s: StudentProfile) -> StudentDTO:
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


def to_student_overview(a: Account) -> StudentOverview:
    last = a.get_last_payment()

    return StudentOverview(
        student=to_student_dto(a.student),
        balance=a.balance.amount,
        movements=[to_movement_dto(m) for m in a.effective()],
        last_payment=to_movement_dto(last) if last else None,
    )
