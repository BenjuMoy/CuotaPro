import logging

from application.application_service import AccountingService, StudentService
from application.cqrs import CQRSService
from application.events import EventBus
from application.maintenance_service import MaintenanceService
from bootstrap.containers import DatabaseBundle, ServiceContainer

logger = logging.getLogger(__name__)


class ServiceFactory:
    def create(self, db_bundle: DatabaseBundle) -> ServiceContainer:
        events = EventBus()

        student_service = StudentService(db_bundle.uow, events)

        accounting_service = AccountingService(db_bundle.uow, events)

        cqrs = CQRSService(db_bundle.uow)

        maintenance_service = MaintenanceService(db_bundle.db, db_bundle.config)

        return ServiceContainer(
            student=student_service,
            accounting=accounting_service,
            cqrs=cqrs,
            event=events,
            maintenance=maintenance_service,
        )
