from domain.student.values import (
    Book,
    Course,
    MonthlyFee,
    PhoneNumber,
    SchoolYear,
    StudentName,
    Teacher,
)

# last_name, first_name, telefons, school, year, teacher, book, course, monthly_fee, balance

# TODO Make this more passive, this is not the aggregate, this is pure data holder

# TODO Make ContactInfo, AcademicInfo, etc?

# TODO make ID only int?


class StudentProfile:
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
        teacher: Teacher,
        monthly_fee: MonthlyFee,
        phone2: PhoneNumber | None = None,
        phone3: PhoneNumber | None = None,
        school: str | None = None,
        school_year: SchoolYear | None = None,
        book: Book | None = None,
        course: Course | None = None,
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

    # -------------------------
    # REHYDRATION (NO validation)
    # -------------------------

    @classmethod
    def from_persistence(
        cls,
        *,
        id: int,
        active: bool,
        name: StudentName,
        phone1: PhoneNumber,
        phone2: PhoneNumber | None,
        phone3: PhoneNumber | None,
        school: str,
        school_year: SchoolYear | None,
        book: Book | None,
        course: Course | None,
        teacher: Teacher,
        monthly_fee: MonthlyFee,
    ):
        obj = cls.__new__(cls)

        obj.id = id
        obj.name = name
        obj.phone1 = phone1
        obj.phone2 = phone2
        obj.phone3 = phone3
        obj.teacher = teacher
        obj.school = school
        obj.school_year = school_year
        obj.book = book
        obj.course = course
        obj.monthly_fee = monthly_fee
        obj.active = active

        return obj
