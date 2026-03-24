from dataclasses import dataclass

from app.services.accounting_service import AccountingService
from app.services.maintenance_service import MaintenanceService
from app.services.reporting_service import ReportingService
from app.services.student_service import StudentService


@dataclass(frozen=True)
class ServiceContainer:
    student: StudentService
    accounting: AccountingService
    reporting: ReportingService
    maintenance: MaintenanceService
