import logging

from app.controllers.main_controller import AppController
from app.database.config import DatabaseConfig
from app.database.connection import DatabaseManager
from app.database.migrations import migrate
from app.database.schema import bootstrap_database
from app.repositories.movement_repository import MovementRepository
from app.repositories.student_repository import StudentRepository
from app.services.accounting_service import AccountingService
from app.services.maintenance_service import MaintenanceService
from app.services.service_container import ServiceContainer
from app.services.student_service import StudentService

logger = logging.getLogger(__name__)


class AppInitializer:
    """
    Responsible for:
    - Preparing database
    - Running migrations
    - Wiring dependencies
    - Returning configured controller
    """

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.db = DatabaseManager(db_config)

    # ------------------------
    # PUBLIC ENTRY POINT
    # ------------------------

    def initialize(self) -> AppController:
        logger.info("Preparing database")
        self._prepare_database()

        logger.info("Building services")
        services = self._build_services()
        return AppController(services)

    # ------------------------
    # INTERNAL STEPS
    # ------------------------

    def _prepare_database(self):
        db_exists = self.db_config.db_path.exists()

        if not db_exists:
            self.db_config.db_path.touch()

        with self.db.transaction() as conn:
            if not db_exists:
                bootstrap_database(conn)
            else:
                migrate(conn)

    def _build_services(self) -> ServiceContainer:
        student_repo = StudentRepository(self.db)
        movement_repo = MovementRepository(self.db)

        student_service = StudentService(student_repo)
        accounting_service = AccountingService(movement_repo, student_repo)
        maintenance_service = MaintenanceService(self.db)

        return ServiceContainer(
            student=student_service,
            accounting=accounting_service,
            maintenance=maintenance_service,
        )

    def shutdown(self):
        self.db.close()
