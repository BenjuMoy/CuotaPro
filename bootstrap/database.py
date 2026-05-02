import logging

from bootstrap.containers import DatabaseBundle
from infrastructure.config.database_config import DatabaseConfig
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.migrations import migrate
from infrastructure.database.schema import (
    SCHEMA_VERSION,
    bootstrap_database,
    get_schema_version,
)
from infrastructure.database.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    def init(self) -> DatabaseBundle:
        config = DatabaseConfig()
        config.ensure_dirs()

        db = DatabaseManager(config.database_path)
        uow = UnitOfWork(db)

        logger.info("Initializing database schema")
        with db.transaction() as conn:
            version = get_schema_version(conn)

            if version == 0:
                logger.info("Running bootstrap_database")
                bootstrap_database(conn)
                version = get_schema_version(conn)

            if version < SCHEMA_VERSION:
                logger.info("Running migrations")
                migrate(conn, version)
                version = get_schema_version(conn)

            if version > SCHEMA_VERSION:
                raise RuntimeError("Database version is newer than app")

        logger.info("Database ready")
        return DatabaseBundle(db, config, uow)
