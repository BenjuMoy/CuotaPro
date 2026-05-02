from domain.shared.exceptions import AppValidationError, BusinessRuleError
from domain.student.values import MonthlyFee, PhoneNumber, StudentName

# last_name, first_name, telefons, school, year, teacher, book, course, monthly_fee, balance

# TODO Make this more passive, this is not the aggregate

VALID_TEACHERS = {"Asuncion", "Daniela", "Florencia", "Kiana", "Romina", "Silvia"}
VALID_SCHOOL_YEARS = {
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
}
VALID_BOOKS = {
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
}
VALID_COURSES = {
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
}


class Student:
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
        school_year: Academic year (optional)
        monthly_fee: Monthly fee amount (> 0)
    """

    def __init__(
        self,
        name: StudentName,
        phone1: PhoneNumber,
        teacher: str,
        monthly_fee: MonthlyFee,
        phone2: PhoneNumber | None = None,
        phone3: PhoneNumber | None = None,
        school: str = "",
        school_year: str = "",
        book: str = "",
        course: str = "",
        active: bool = True,
        id: int | None = None,
    ):
        self.id = id
        self.name = name
        self.phone1 = phone1
        self.phone2 = phone2
        self.phone3 = phone3
        self.teacher = teacher
        self.school = school
        self.school_year = school_year
        self.book = book
        self.course = course
        self.monthly_fee = monthly_fee
        self.active = active

        self._validate()

    def change_monthly_fee(self, new_fee: MonthlyFee):
        if self.monthly_fee.amount == new_fee.amount:
            raise BusinessRuleError("Las cuotas no pueden ser iguales")

        if new_fee.amount < self.monthly_fee.amount:
            raise BusinessRuleError("La cuota nueva no puede ser menor que la vieja")

        self.monthly_fee = new_fee

    def _validate(self):
        if self.teacher not in VALID_TEACHERS:
            raise AppValidationError("Profesor invalido")

        if self.school_year not in VALID_SCHOOL_YEARS:
            raise AppValidationError("Año escolar invalido")

        if self.book not in VALID_BOOKS:
            raise AppValidationError("Libro invalido")

        if self.course not in VALID_SCHOOL_YEARS:
            raise AppValidationError("curso invalido")
