from app.models.models import Student
from app.repositories.student_repository import StudentRepository


class StudentService:
    def __init__(self, student_repo: StudentRepository):
        self.repo = student_repo

    def add(self, data: dict[str, str | int | bool]) -> Student:
        """Adds a student to the database."""
        # Validate model first (outside transaction)
        new_student = Student.model_validate(dict(data))

        saved_student = self.repo.add(new_student)

        return saved_student

    def update(self, student_id: int, data: dict[str, str | int | bool]) -> Student:
        """Updates a student, updates state, and saves."""
        # Get student
        existing_student = self.repo.get_by_id(student_id)

        # Create copy and update copy
        updated_student_data = existing_student.model_dump()
        updated_student_data.update(data)

        # Validate and create the new model instance
        updated_student = Student.model_validate(dict(updated_student_data))
        self.repo.update(updated_student)

        return updated_student

    def switch_state(self, student_id: int) -> Student:
        """Handles the state switch."""
        student = self.repo.get_by_id(student_id)
        updated = student.model_copy(update={"active": not student.active})
        new_student = self.repo.update(updated)

        return new_student

    # Getters

    def get_all(self) -> list[Student]:
        """Get all students from db."""
        return self.repo.get_all()

    def get_all_active(self) -> list[Student]:
        return self.repo.get_all_active_students()

    def get_by_id(self, student_id: int) -> Student:
        """Retrieves a single student by their ID."""
        return self.repo.get_by_id(student_id)

    def get_debtors(self) -> list[Student]:
        """Search students by debt."""
        return self.repo.get_debtors()

    def search_by_name(self, name: str) -> list[Student]:
        """Search students by name."""
        return self.repo.search_by_name(name)

    def search_by_teacher(self, teacher_name: str) -> list[Student]:
        """Search students by teacher name."""
        return self.repo.search_by_teacher(teacher_name)

    def count_by_monthly_fee(self, monthly_fee: int) -> int:
        """Search students by monthly fee."""
        return self.repo.count_students_by_monthly_fee(monthly_fee)

    def get_active_count(self) -> int:
        return self.repo.get_active_student_count()

    def get_fees_list(self) -> list[tuple[int, int]]:
        return self.repo.get_fees_list()
