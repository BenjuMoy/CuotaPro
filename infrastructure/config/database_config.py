from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    main_dir: Path = Path.home() / "CuotaPro"
    database_dir: Path = main_dir / "data"
    database_path: Path = database_dir / "student_management.db"
    backup_dir: Path = database_dir / "backup"
    export_dir: Path = database_dir / "exports"

    def ensure_dirs(self) -> None:
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
