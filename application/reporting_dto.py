from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DashboardMetrics:
    active_students: int
    expected_income: int
    collected: int
    total_debt: int


@dataclass(frozen=True, slots=True)
class StudentFeeDetail:
    first_name: str
    last_name: str
    monthly_fee: int


@dataclass(frozen=True, slots=True)
class SalaryReport:
    teacher: str
    total: int
    student_count: int
    details: list[StudentFeeDetail]
