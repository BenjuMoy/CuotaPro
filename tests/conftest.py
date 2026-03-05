from pathlib import Path

import pytest

from app.database.config import DatabaseConfig
from app.database.connection import DatabaseManager
from app.database.migrations import migrate
from app.database.schema import bootstrap_database
from app.services.service_container import ServiceContainer


@pytest.fixture
def db():
    config = DatabaseConfig(db_path=":memory:")
    db = DatabaseManager(config)

    # Prepare schema
    with db.transaction() as conn:
        bootstrap_database(conn)

    yield db

    db.close()


@pytest.fixture
def repositories(db: DatabaseManager):
    from app.repositories.movement_repository import MovementRepository
    from app.repositories.student_repository import StudentRepository

    return {
        "student": StudentRepository(db),
        "movement": MovementRepository(db),
    }


@pytest.fixture
def services(repositories, db: DatabaseManager) -> ServiceContainer:
    from app.services.accounting_service import AccountingService
    from app.services.maintenance_service import MaintenanceService
    from app.services.service_container import ServiceContainer
    from app.services.student_service import StudentService

    student_service = StudentService(repositories["student"])
    accounting_service = AccountingService(
        repositories["movement"], repositories["student"]
    )
    maintenance_service = MaintenanceService(db)

    return ServiceContainer(
        student=student_service,
        accounting=accounting_service,
        maintenance=maintenance_service,
    )
