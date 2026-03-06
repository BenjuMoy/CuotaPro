from pathlib import Path
from sqlite3 import Connection

from app.utils.constantes import (
    DATABASE_BACKUP_DIR,
    DATABASE_DIR,
    DATABASE_EXPORT_DIR,
    DATABASE_PATH,
)


class DatabaseConfig:
    def __init__(
        self,
        db_path: Path | str = Path(DATABASE_PATH),
        db_dir: Path = Path(DATABASE_DIR),
        backup_dir: Path = Path(DATABASE_BACKUP_DIR),
        export_dir: Path = Path(DATABASE_EXPORT_DIR),
    ):
        self.db_path = db_path
        self.db_dir = db_dir
        self.db_backup_dir = backup_dir
        self.db_export_dir = export_dir

    def apply_pragmas(self, connection: Connection):
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA synchronous = NORMAL;")
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute("PRAGMA wal_autocheckpoint = 1000;")
