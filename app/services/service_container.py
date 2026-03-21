from app.services.accounting_service import AccountingService
from app.services.maintenance_service import MaintenanceService
from app.services.reporting_service import ReportingService
from app.services.student_service import StudentService


class ServiceContainer:
    def __init__(
        self,
        student: StudentService,
        accounting: AccountingService,
        reporting: ReportingService,
        maintenance: MaintenanceService,
    ):
        self.student = student
        self.accounting = accounting
        self.reporting = reporting
        self.maintenance = maintenance
