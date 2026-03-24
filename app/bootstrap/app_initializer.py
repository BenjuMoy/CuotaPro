import logging
from dataclasses import dataclass

from app.database.config import DatabaseConfig
from app.database.connection import DatabaseManager
from app.database.migrations import migrate
from app.database.schema import bootstrap_database, database_initialized
from app.repositories.movement_repository import MovementRepository
from app.repositories.student_repository import StudentRepository
from app.services.accounting_service import AccountingService
from app.services.maintenance_service import MaintenanceService
from app.services.reporting_service import ReportingService
from app.services.service_container import ServiceContainer
from app.services.student_service import StudentService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Repositories:
    student: StudentRepository
    movement: MovementRepository


class AppInitializer:
    """
    Responsible for:
    - Preparing database
    - Running migrations
    - Wiring dependencies
    - Returning configured main service
    """

    def __init__(self, db_config: DatabaseConfig):
        self.db = DatabaseManager(db_config)

    # ------------------------
    # PUBLIC ENTRY POINT
    # ------------------------

    def initialize(self) -> ServiceContainer:
        logger.info("Preparing database")
        self._prepare_database()

        logger.info("Building services")
        services = self._build_services()
        return services

    # ------------------------
    # INTERNAL STEPS
    # ------------------------

    def _prepare_database(self):
        """bootstrap database or migrates if exists"""

        with self.db.transaction() as conn:
            if not database_initialized(conn):
                bootstrap_database(conn)

            else:
                migrate(conn)

    def _build_services(self) -> ServiceContainer:
        repos = Repositories(student=StudentRepository(), movement=MovementRepository())

        student_service = StudentService(repos.student, self.db)

        accounting_service = AccountingService(
            student_repo=repos.student, movement_repo=repos.movement, db=self.db
        )

        reporting_service = ReportingService(repos.student, repos.movement, self.db)
        maintenance_service = MaintenanceService(self.db)

        return ServiceContainer(
            student=student_service,
            accounting=accounting_service,
            reporting=reporting_service,
            maintenance=maintenance_service,
        )

    def _build_repositories(self):
        return StudentRepository(), MovementRepository()
