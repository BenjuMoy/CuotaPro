from pydantic_core import ValidationError

from app.models.models import Student
from app.models.reportes import SalaryReport
from app.repositories.student_repository import StudentRepository


class StudentService:
    def __init__(self, student_repo: StudentRepository):
        self.student_repo = student_repo

    # Students

    def add(self, data: dict) -> Student:
        """Adds a student to the database."""
        # Validate model first (outside transaction)
        try:
            new_student = Student.model_validate(dict(data))
        except ValidationError as e:
            raise ValidationError(e)

        with self.student_repo.db_manager.transaction() as conn:
            saved_student = self.student_repo.add(new_student, conn)

        return saved_student

    def update(self, student_id: int, data: dict) -> Student:
        """Updates a student, updates state, and saves."""
        with self.student_repo.db_manager.transaction() as conn:
            # Get student
            existing_student = self.student_repo.get_by_id(student_id, conn)

            # Create copy and update copy
            updated_student_data = existing_student.model_dump()
            updated_student_data.update(data)

            # Validate and create the new model instance
            updated_student = Student.model_validate(dict(updated_student_data))
            self.student_repo.update(updated_student, conn)

        return updated_student

    def switch_state(self, student_id: int) -> Student:
        """Handles the state switch."""
        with self.student_repo.db_manager.transaction() as conn:
            student = self.student_repo.get_by_id(student_id, conn)
            updated = student.model_copy(update={"active": not student.active})
            new_student = self.student_repo.update(updated, conn)

        return new_student

    # Getters

    def get_all(self) -> list[Student]:
        """Get all students from student_repo.db_manager."""
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.get_all(conn)

    def get_all_active(self) -> list[Student]:
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.get_all_active_students(conn)

    def get_by_id(self, student_id: int) -> Student:
        """Retrieves a single student by their ID."""
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.get_by_id(student_id, conn)

    def get_debtors(self) -> list:
        """Search students by debt."""
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.get_debtors(conn)

    def search_by_name(self, name: str) -> list[Student]:
        """Search students by name."""
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.search_by_name(name, conn)

    def search_by_teacher(self, teacher_name: str) -> list[Student]:
        """Search students by teacher name."""
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.search_by_teacher(teacher_name, conn)

    def count_by_monthly_fee(self, monthly_fee: int) -> int:
        """Search students by monthly fee."""
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.count_students_by_monthly_fee(monthly_fee, conn)

    def get_active_count(self) -> int:
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.get_active_student_count(conn)

    def get_fees_list(self) -> list[tuple[int, int]]:
        with self.student_repo.db_manager.transaction() as conn:
            return self.student_repo.get_fees_list(conn)

    # Reports

    def get_salary(self, professor_name: str):
        """
        Calculates the total payment for a specific professor based on active student fees.

        Returns:
            dict: {
                'professor': str,
                'total': int,
                'student_count': int,
                'details': list[dict]  # Each dict contains student name and fee
            }

        Raises:
            ValueError: If professor is not found or has no students.
        """
        with self.student_repo.db_manager.transaction() as conn:
            student_list = self.student_repo.get_all_active_students(conn)
            report = SalaryReport(student_list)
            return report.generar_salario_teacher(professor_name)
