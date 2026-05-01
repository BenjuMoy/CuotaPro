from domain.shared.exceptions import BusinessRuleError
from domain.student.values import MonthlyFee, PhoneNumber, StudentName

# last_name, first_name, telefons, school, year, teacher, book, course, monthly_fee, balance

# TODO Make this more passive, this is not the aggregate


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

    def change_monthly_fee(self, new_fee: MonthlyFee):
        if self.monthly_fee.amount == new_fee.amount:
            raise BusinessRuleError("Las cuotas no pueden ser iguales")

        if new_fee.amount < self.monthly_fee.amount:
            raise BusinessRuleError("La cuota nueva no puede ser menor que la vieja")

        self.monthly_fee = new_fee

    def ensure_active(self):
        if not self.active:
            raise BusinessRuleError("Estudiante inactivo")
