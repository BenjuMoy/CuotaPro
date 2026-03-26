from dataclasses import dataclass
from pathlib import Path

from app.utils.constantes import (
    DATABASE_BACKUP_DIR,
    DATABASE_DIR,
    DATABASE_EXPORT_DIR,
    DATABASE_PATH,
)


@dataclass(frozen=True)
class DatabaseConfig:
    db_path: Path = Path(DATABASE_PATH)
    db_dir: Path = Path(DATABASE_DIR)
    db_backup_dir: Path = Path(DATABASE_BACKUP_DIR)
    db_export_dir: Path = Path(DATABASE_EXPORT_DIR)

    def ensure_directories_exist(self):
        """Utility to create necessary directories."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_export_dir.mkdir(parents=True, exist_ok=True)
