from collections import defaultdict
from datetime import datetime

from app.models.models import DashboardMetrics, Student
from app.models.reportes import SalaryReport
from app.repositories.movement_repository import MovementRepository
from app.repositories.student_repository import StudentRepository


class ReportingService:
    def __init__(
        self,
        student_repo: StudentRepository,
        movement_repo: MovementRepository,
    ):
        self.students = student_repo
        self.movements = movement_repo

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
        student_list = self.students.get_all_active_students()
        report = SalaryReport(student_list)
        return report.generar_salario_teacher(professor_name)

    def get_kpi_metrics(self) -> DashboardMetrics:
        now = datetime.now()

        collected = self.movements.total_collected_this_month(now.month, now.year)

        students = self.students.get_all_active_students()
        balances = self.movements.get_balances_for_students()

        expected = sum(s.monthly_fee for s in students)

        debt_total = sum(balances.get(s.id, 0) for s in students)

        return DashboardMetrics(
            active_students=len(students),
            expected_income=expected,
            collected=collected,
            total_debt=debt_total,
        )

    def get_graphic_metrics(self):
        income_by_month = defaultdict(int)

        balances = self.movements.get_balances_for_students()
        income_by_month = self.movements.get_income_by_month()

        students = self.students.get_all_active_students()

        # Income dist
        months_sorted = self.get_income_trend(income_by_month)

        # teacher count
        teacher_sorted = self.get_teacher_distribution(students)

        # Debt bucket
        debt_buckets = self.get_debt_distribution(students, balances)

        return months_sorted, teacher_sorted, debt_buckets

    def get_income_trend(self, income_by_month: dict[tuple[int, int], int]):
        months_sorted = dict(sorted(income_by_month.keys())[-6:])
        return months_sorted

    def get_teacher_distribution(self, students: list[Student]):
        teacher_count = defaultdict(int)

        for s in students:
            teacher_count[s.teacher] += 1

        teacher_sorted = dict(sorted(teacher_count.items(), key=lambda x: x[1]))

        return teacher_sorted

    def get_debt_distribution(self, students: list[Student], balances: dict[int, int]):
        debt_buckets = {
            "Al día": 0,
            "1 mes": 0,
            "2 meses": 0,
            "3+ meses": 0,
        }

        for s in students:
            if s.id not in balances:
                continue

            balance = balances[s.id]

            if balance >= 0:
                debt_buckets["Al día"] += 1
                continue

            months = abs(balance) // s.monthly_fee

            if months == 1:
                debt_buckets["1 mes"] += 1
            elif months == 2:
                debt_buckets["2 meses"] += 1
            else:
                debt_buckets["3+ meses"] += 1

        return debt_buckets
