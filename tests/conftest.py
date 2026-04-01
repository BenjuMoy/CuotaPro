from pathlib import Path

import pytest

from app.database.config import DatabaseConfig
from app.database.connection import DatabaseManager
from app.database.schema import bootstrap_database
from app.repositories.movement_repository import MovementRepository
from app.repositories.student_repository import StudentRepository
from app.services.accounting_service import AccountingService
from app.services.reporting_service import ReportingService
from app.services.student_service import StudentService


@pytest.fixture
def db_config(tmp_path: Path) -> DatabaseConfig:
    return DatabaseConfig(
        db_path=tmp_path / "test.db",
        db_dir=tmp_path,
        db_backup_dir=tmp_path / "backup",
        db_export_dir=tmp_path / "export",
    )


@pytest.fixture
def db_manager(db_config: DatabaseConfig) -> DatabaseManager:
    db_config.ensure_directories_exist()
    db = DatabaseManager(db_config)

    with db.transaction() as conn:
        bootstrap_database(conn)

    return db


@pytest.fixture
def student_repo(db_manager: DatabaseManager) -> StudentRepository:
    return StudentRepository(db_manager)


@pytest.fixture
def movement_repo(db_manager: DatabaseManager) -> MovementRepository:
    return MovementRepository(db_manager)


@pytest.fixture
def student_service(student_repo: StudentRepository) -> StudentService:
    return StudentService(student_repo)


@pytest.fixture
def accounting_service(
    student_repo: StudentRepository,
    movement_repo: MovementRepository,
) -> AccountingService:
    return AccountingService(student_repo, movement_repo)


@pytest.fixture
def reporting_service(
    student_repo: StudentRepository,
    movement_repo: MovementRepository,
) -> ReportingService:
    return ReportingService(student_repo, movement_repo)
