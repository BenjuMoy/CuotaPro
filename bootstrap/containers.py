from dataclasses import dataclass

from application.application_service import AccountingService, StudentService
from application.cqrs import CQRSService
from application.events import EventBus
from application.maintenance_service import MaintenanceService
from domain.accounting.repository import MovementRepository
from domain.student.repository import StudentRepository
from infrastructure.config.database_config import DatabaseConfig
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class ServiceContainer:
    student: StudentService
    accounting: AccountingService
    cqrs: CQRSService
    maintenance: MaintenanceService
    event: EventBus


@dataclass(frozen=True, slots=True)
class Repositories:
    student: StudentRepository
    movement: MovementRepository


@dataclass(slots=True)
class DatabaseBundle:
    db: DatabaseManager
    config: DatabaseConfig
    uow: UnitOfWork
