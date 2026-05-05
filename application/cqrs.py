"""
CQRS Read Services

Purpose:
- Provide read-only access to application data
- Optimize for queries and reporting
- Avoid domain logic and aggregates where possible

Guidelines:
- Prefer database-level aggregation
- Avoid loading full aggregates unless necessary
- Return DTOs, never domain objects
"""

from application.dto import MovementDTO, StudentDTO, StudentOverview
from application.mappers import to_movement_dto, to_student_dto, to_student_overview
from application.reporting_dto import DashboardMetrics, SalaryReport
from core.clock import Clock
from domain.account.model import Account
from domain.accounting.values import Period
from domain.shared.exceptions import ApplicationError
from domain.shared.shared import PeriodBalance
from infrastructure.database.unit_of_work import UnitOfWork


class CQRSService:
    """
    ### CQRS Read Model

    The read model is optimized for queries and reporting.

    Rules:
    - Must NOT use domain aggregates
    - Must NOT enforce business rules
    - Should prefer SQL aggregation
    - Returns DTOs or primitives only
    """

    def __init__(self, uow: UnitOfWork, clock: Clock | None = None):
        self.uow = uow
        self.clock = clock or Clock()

    # --- Student CQRS --- #

    def get_all_students(self) -> list[StudentDTO]:
        with self.uow as uow:
            return [to_student_dto(s) for s in uow.students.get_all()]

    def get_by_id(self, student_id: int) -> StudentDTO:
        with self.uow as uow:
            return to_student_dto(uow.students.get_by_id(student_id))

    def get_overview_by_id(self, student_id: int) -> StudentOverview:
        with self.uow as uow:
            return to_student_overview(uow.accounts.get(student_id))

    def search_students(
        self,
        name: str | None = None,
        teacher: str | None = None,
        active: bool | None = None,
        only_debtors: bool | None = None,
    ) -> list[StudentOverview]:
        with self.uow as uow:
            students = uow.students.search_students(
                name=name, teacher=teacher, active=active
            )
            ids = [s.id for s in students]
            accounts = uow.accounts.get_many(ids)

        if not students:
            return []

        if only_debtors:
            accounts = [acc for acc in accounts if acc.has_debt()]

        return [to_student_overview(acc) for acc in accounts]

    def count_by_monthly_fee(self, monthly_fee: int) -> int:
        with self.uow as uow:
            return uow.students.count_by_monthly_fee(monthly_fee)

    def get_active_count(self) -> int:
        with self.uow as uow:
            return uow.students.count_active()

    def get_fees_list(self) -> list[tuple[int, int]]:
        with self.uow as uow:
            return uow.students.get_fees_list()

    # --- Accounting CQRS --- #

    def get_unpaid_months_with_debt(self, student_id: int) -> list[PeriodBalance]:
        with self.uow as uow:
            return uow.accounts.get(student_id).unpaid_periods()

    def get_all_movements(self) -> list[MovementDTO]:
        with self.uow as uow:
            return [to_movement_dto(m) for m in uow.movements.get_all()]

    def get_last_fee_date(self) -> Period | None:
        with self.uow as uow:
            return uow.movements.get_last_date_applied_fee()

    def get_students_without_fee(self, month: int, year: int) -> list[StudentDTO]:
        with self.uow as uow:
            ids = uow.reports.get_students_without_fee(month, year)
            students = uow.students.list_by_ids(ids)

        return [to_student_dto(s) for s in students]

    def preview_fee_application(self, month: int, year: int) -> int:
        return len(self.get_students_without_fee(month, year))

    def are_fees_applied(self) -> bool:
        now = self.clock.now()

        with self.uow as uow:
            return uow.reports.are_fees_applied(now.month, now.year)

    # --- Reporting --- #

    def get_salary(self, teacher_name: str) -> SalaryReport:
        with self.uow as uow:
            count, total = uow.reports.get_salary(teacher_name)

        if count == 0:
            raise ApplicationError("No hay estudiantes activos para este profesor")

        return SalaryReport(
            teacher=teacher_name,
            total=total,
            student_count=count,
            details=[],  # optionally fetch separately
        )

    def get_kpi_metrics(self) -> DashboardMetrics:
        """
        Returns dashboard KPIs for the current month.

        Metrics:
        - active_students: number of active accounts
        - expected_income: sum of monthly fees
        - collected: payments received this month
        - total_debt: total outstanding debt

        Note:
        Currently computed in-memory. Should be moved to DB aggregation.
        """
        now = self.clock.now()
        with self.uow as uow:
            active, expected, collected, debt = uow.reports.get_kpi_metrics(
                now.month, now.year
            )

        return DashboardMetrics(
            active_students=active,
            expected_income=expected,
            collected=collected,
            total_debt=debt,
        )

    def get_graphic_metrics(self):
        with self.uow as uow:
            accounts = uow.accounts.list_active_accounts()

        return (
            self.get_income_trend(accounts),
            self.get_teacher_distribution(),
            self.get_debt_distribution(),
        )

    def get_income_trend(self, accounts: list[Account]) -> dict[tuple[int, int], int]:
        with self.uow as uow:
            rows = uow.reports.get_income_trend()

        return {(m, y): total for m, y, total in rows}

    def get_teacher_distribution(self) -> dict[str, int]:
        with self.uow as uow:
            return uow.reports.get_teacher_distribution()

    def get_debt_distribution(self) -> dict[str, int]:
        with self.uow as uow:
            return uow.reports.get_debt_distribution()
