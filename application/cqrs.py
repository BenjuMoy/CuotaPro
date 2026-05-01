from collections import Counter

from application.dto import MovementDTO, StudentDTO, StudentOverview
from application.mappers import to_movement_dto, to_student_dto, to_student_overview
from application.reporting_dto import DashboardMetrics, SalaryReport, StudentFeeDetail
from core.clock import Clock
from domain.accounting.model import MovementType
from domain.accounting.values import Period
from domain.shared.shared import PeriodBalance
from domain.student.model import Student
from domain.student_account.model import StudentAccount
from infrastructure.database.unit_of_work import UnitOfWork


class CQRSService:
    def __init__(self, uow: UnitOfWork, clock: Clock | None = None):
        self.uow = uow
        self.clock = clock or Clock()

    # --- Helpers --- #

    def _build_account(self, student_id: int, uow: UnitOfWork) -> StudentAccount:
        student = uow.students.get_by_id(student_id)
        movements = uow.movements.list_by_student_id(student_id)
        return StudentAccount(student, movements)

    def _build_accounts_bulk(
        self, students: list[Student], uow: UnitOfWork
    ) -> list[StudentAccount]:
        ids = [s.id for s in students]
        movements = uow.movements.list_by_students_ids(ids)

        by_student: dict[int, list] = {}
        for m in movements:
            by_student.setdefault(m.student_id, []).append(m)

        return [StudentAccount(s, by_student.get(s.id, [])) for s in students]

    # --- Student CQRS --- #

    def get_all_students(self) -> list[StudentDTO]:
        with self.uow as uow:
            return [to_student_dto(s) for s in uow.students.get_all()]

    def get_by_id(self, student_id: int) -> StudentDTO:
        with self.uow as uow:
            return to_student_dto(uow.students.get_by_id(student_id))

    def get_overview_by_id(self, student_id: int) -> StudentOverview:
        with self.uow as uow:
            return to_student_overview(self._build_account(student_id, uow))

    def search_students(
        self,
        name: str | None = None,
        teacher: str | None = None,
        active: bool | None = None,
        only_debtors: bool | None = None,
    ) -> dict[int, StudentOverview]:

        with self.uow as uow:
            students = uow.students.search_students(
                name=name, teacher=teacher, active=active
            )
            accounts = self._build_accounts_bulk(students, uow)

        if not students:
            return {}

        if only_debtors:
            accounts = [acc for acc in accounts if acc.has_debt()]

        return {
            acc.student.id: to_student_overview(acc)
            for acc in accounts
            if acc.student.id
        }

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
            return self._build_account(student_id, uow).unpaid_periods()

    def get_all_movements(self) -> list[MovementDTO]:
        with self.uow as uow:
            return [to_movement_dto(m) for m in uow.movements.get_all()]

    def get_last_fee_date(self) -> Period | None:
        with self.uow as uow:
            return uow.movements.get_last_date_applied_fee()

    def get_students_without_fee(self, month: int, year: int) -> list[StudentDTO]:
        period = Period(month, year)
        with self.uow as uow:
            students = uow.students.list_active()
            accounts = self._build_accounts_bulk(students, uow)

        return [
            to_student_dto(acc.student) for acc in accounts if not acc.has_fee(period)
        ]

    def preview_fee_application(self, month: int, year: int) -> int:
        return len(self.get_students_without_fee(month, year))

    def are_fees_applied(self) -> bool:
        now = self.clock.now()
        period = Period(now.month, now.year)

        with self.uow as uow:
            students = uow.students.list_active()
            accounts = self._build_accounts_bulk(students, uow)

        return all(acc.has_fee(period) for acc in accounts)

    # Wrappers

    def get_bulk_overview_data(self, ids: list[int]) -> dict[int, StudentOverview]:

        if not ids:
            return {}

        with self.uow as uow:
            students = uow.students.list_by_ids(ids)
            movements = uow.movements.list_by_students_ids(ids)

        movements_by_student: dict[int, list] = {}
        for m in movements:
            movements_by_student.setdefault(m.student_id, []).append(m)

        result = {}

        for s in students:
            student_movements = movements_by_student.get(s.id, [])
            account = StudentAccount(s, student_movements)
            result[s.id] = to_student_overview(account)

        return result

    # --- Reporting --- #

    def get_salary(self, teacher_name: str) -> SalaryReport:
        with self.uow as uow:
            students = [
                s for s in uow.students.list_active() if s.teacher == teacher_name
            ]

        if not students:
            raise ValueError(
                f"No se encontraron estudiantes activos para el profesor: {teacher_name}"
            )

        details: list[StudentFeeDetail] = [
            StudentFeeDetail(
                last_name=s.name.last_name,
                first_name=s.name.first_name,
                monthly_fee=s.monthly_fee.amount,
            )
            for s in students
        ]

        total = sum(s.monthly_fee.amount for s in students)

        return SalaryReport(
            teacher=teacher_name,
            total=total,
            student_count=len(students),
            details=details,
        )

    def get_kpi_metrics(self) -> DashboardMetrics:
        now = self.clock.now()
        with self.uow as uow:
            students = uow.students.list_active()
            accounts = self._build_accounts_bulk(students, uow)

        expected = sum(s.monthly_fee.amount for s in students)

        total_debt = sum(abs(acc.balance.amount) for acc in accounts if acc.has_debt())

        collected = sum(
            acc.total_paid_in_period(Period(now.month, now.year)) for acc in accounts
        )

        return DashboardMetrics(
            active_students=len(students),
            expected_income=expected,
            collected=collected,
            total_debt=total_debt,
        )

    def get_graphic_metrics(self):
        with self.uow as uow:
            students = uow.students.list_active()
            accounts = self._build_accounts_bulk(students, uow)

        return (
            self.get_income_trend(accounts),
            self.get_teacher_distribution(students),
            self.get_debt_distribution(accounts),
        )

    def get_income_trend(self, accounts: list[StudentAccount]):
        from collections import defaultdict

        buckets = defaultdict(int)

        for acc in accounts:
            for m in acc.effective():
                if m.type == MovementType.PAYMENT:
                    key = m.period.month, m.period.year
                    buckets[key] += m.amount.amount

        sorted_items = sorted(buckets.items(), key=lambda x: (x[0][1], x[0][0]))
        return dict(sorted_items[-6:])

    def get_teacher_distribution(self, students: list[Student]):
        counts = Counter(s.teacher for s in students)
        return {k: int(v) for k, v in sorted(counts.items(), key=lambda x: x[1])}

    def get_debt_distribution(self, accounts: list[StudentAccount]):
        import math

        buckets = {"Al día": 0, "1 mes": 0, "2 meses": 0, "3+ meses": 0}

        for acc in accounts:
            balance = acc.balance.amount

            if balance >= 0:
                buckets["Al día"] += 1

            else:
                fee = acc.student.monthly_fee.amount

                if fee > 0:
                    months = math.ceil(abs(balance) / fee)

                    if months == 1:
                        buckets["1 mes"] += 1
                    elif months == 2:
                        buckets["2 meses"] += 1
                    else:
                        buckets["3+ meses"] += 1

        return buckets
