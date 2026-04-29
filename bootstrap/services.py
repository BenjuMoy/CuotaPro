import logging

from application.application_service import AccountingService, StudentService
from application.cqrs import CQRSService
from application.events import EventBus
from application.maintenance_service import MaintenanceService
from bootstrap.containers import DatabaseBundle, Repositories, ServiceContainer
from domain.accounting.repository import MovementRepository
from domain.student.repository import StudentRepository
from infrastructure.database.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ServiceFactory:
    def create(self, db_bundle: DatabaseBundle) -> ServiceContainer:
        repos = self._build_repositories(db_bundle.uow)

        events = EventBus()

        student_service = StudentService(db_bundle.uow, events, repos.student)

        accounting_service = AccountingService(
            db_bundle.uow, events, repos.student, repos.movement
        )

        cqrs = CQRSService(db_bundle.uow, repos.student, repos.movement)

        maintenance_service = MaintenanceService(db_bundle.db, db_bundle.config)

        return ServiceContainer(
            student=student_service,
            accounting=accounting_service,
            cqrs=cqrs,
            event=events,
            maintenance=maintenance_service,
        )

    def _build_repositories(self, uow: UnitOfWork) -> Repositories:
        return Repositories(
            student=StudentRepository(uow), movement=MovementRepository(uow)
        )
