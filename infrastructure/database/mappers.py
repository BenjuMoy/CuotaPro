from sqlite3 import Row

from domain.accounting.model import Movement
from domain.accounting.values import Money, Period
from domain.shared.shared import MovementType
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

# -------------------------
# STUDENT
# -------------------------


def row_to_student(row: Row) -> Student:
    return Student.from_persistence(
        id=row["id"],
        active=bool(row["active"]),
        name=StudentName(first_name=row["first_name"], last_name=row["last_name"]),
        phone1=PhoneNumber(row["phone1"]),
        phone2=PhoneNumber(row["phone2"]) if row["phone2"] else None,
        phone3=PhoneNumber(row["phone3"]) if row["phone3"] else None,
        teacher=Teacher(row["teacher"]),
        book=Book(row["book"]),
        course=Course(row["course"]),
        school=row["school"],
        school_year=SchoolYear(row["year"]),
        monthly_fee=MonthlyFee(row["monthly_fee"]),
    )


def student_to_params(s: Student) -> dict:
    return {
        "active": int(s.active),
        "last_name": s.name.last_name,
        "first_name": s.name.first_name,
        "phone1": s.phone1.value,
        "phone2": s.phone2.value if s.phone2 else "",
        "phone3": s.phone3.value if s.phone3 else "",
        "teacher": s.teacher.name if s.teacher else "",
        "book": s.book.title if s.book else "",
        "course": s.course.name if s.course else "",
        "school": s.school,
        "year": s.school_year.value if s.school_year else "",
        "monthly_fee": s.monthly_fee.amount,
    }


# -------------------------
# MOVEMENT
# -------------------------


def row_to_movement(row: Row) -> Movement:
    return Movement.from_persistence(
        id=row["id"],
        student_id=row["student_id"],
        type=MovementType(row["type"]),
        amount=Money(row["amount"]),
        period=Period(row["month"], row["year"]),
        reference_id=row["reference_id"],
        created_at=row["created_at"],
    )
