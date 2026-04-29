from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardMetrics:
    active_students: int
    expected_income: int
    collected: int
    total_debt: int


@dataclass(frozen=True)
class StudentFeeDetail:
    first_name: str
    last_name: str
    monthly_fee: int


@dataclass(frozen=True)
class SalaryReport:
    teacher: str
    total: int
    student_count: int
    details: list[StudentFeeDetail]
