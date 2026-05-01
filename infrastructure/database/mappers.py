from sqlite3 import Row

from domain.accounting.model import Movement, MovementType
from domain.accounting.values import Money, Period
from domain.student.model import Student
from domain.student.values import MonthlyFee, PhoneNumber, StudentName

# -------------------------
# STUDENT
# -------------------------


def row_to_student(row: Row) -> Student:
    return Student(
        id=row["id"],
        active=bool(row["active"]),
        name=StudentName(
            first_name=row["first_name"],
            last_name=row["last_name"],
        ),
        phone1=PhoneNumber(row["phone1"]),
        phone2=PhoneNumber(row["phone2"]) if row["phone2"] else None,
        phone3=PhoneNumber(row["phone3"]) if row["phone3"] else None,
        teacher=row["teacher"],
        book=row["book"],
        course=row["course"],
        school=row["school"],
        school_year=row["year"],
        monthly_fee=MonthlyFee(row["monthly_fee"]),
    )


def student_to_params(student: Student) -> dict:
    return {
        "active": int(student.active),
        "last_name": student.name.last_name,
        "first_name": student.name.first_name,
        "phone1": student.phone1.value,
        "phone2": student.phone2.value if student.phone2 else "",
        "phone3": student.phone3.value if student.phone3 else "",
        "teacher": student.teacher,
        "book": student.book,
        "course": student.course,
        "school": student.school,
        "year": student.school_year,
        "monthly_fee": student.monthly_fee.amount,
    }


# -------------------------
# MOVEMENT
# -------------------------


def row_to_movement(row: Row) -> Movement:
    return Movement(
        id=row["id"],
        student_id=row["student_id"],
        movement_type=MovementType(row["type"]),
        amount=Money(row["amount"]),
        period=Period(row["month"], row["year"]),
        reference_id=row["reference_id"],
        created_at=row["created_at"],
    )
