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
        connection.execute("PRAGMA journal_mode = WAL;")  # Enable journal (WAL)
        connection.execute(
            "PRAGMA synchronous = NORMAL;"
        )  # Enable concurrency (NORMAL)
        connection.execute("PRAGMA foreign_keys = ON;")  # Enable Foreign Keys


# Note: If you ever switch to manual file copy (shutil.copy2) while in WAL mode, switch to: PRAGMA wal_checkpoint(FULL);
