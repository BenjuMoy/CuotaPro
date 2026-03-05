import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app.database.connection import DatabaseManager


class MaintenanceService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.config = db_manager.db_config

    # -------------------------
    # BACKUP
    # -------------------------

    def create_backup(self) -> Path:
        """Creates a safe SQLite backup using SQLite backup API."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"student_management_{timestamp}.db"
        backup_path = self.config.db_backup_dir / backup_name

        self.config.db_backup_dir.mkdir(parents=True, exist_ok=True)

        source_conn = self.db.connect()

        dest_conn = sqlite3.connect(backup_path)

        try:
            with dest_conn:
                source_conn.backup(dest_conn)
        finally:
            dest_conn.close()

        self._cleanup_old_backups()
        return backup_path

    # -------------------------
    # List BackUps
    # -------------------------

    def list_backup_files(self) -> list[Path]:
        backup_files = list(self.config.db_backup_dir.glob("student_management_*.db"))
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return backup_files

    # -------------------------
    # RESTORE
    # -------------------------

    def restore_backup(self, file_path: str) -> bool:
        backup_path = Path(file_path)

        if not backup_path.exists():
            return False

        # Safety backup before restore
        self.create_backup()

        # Close active connection
        self.db.close()

        # db_path = Path(self.config.db_path)
        # wal_path = db_path.with_suffix(db_path.suffix + "-wal")
        # shm_path = db_path.with_suffix(db_path.suffix + "-shm")

        ## Remove main DB and WAL artifacts
        # for path in [db_path, wal_path, shm_path]:
        #    if path.exists():
        #        path.unlink()

        # Copy clean backup
        # shutil.copy2(backup_path, db_path)

        with sqlite3.connect(backup_path) as source_conn:
            with sqlite3.connect(self.config.db_path) as dest_conn:
                source_conn.backup(dest_conn)

        return True

    # def restore_backup(self, file_path: str) -> bool: # Old version
    #    """Restores a backup safely."""
    #    backup_path = Path(file_path)

    #    if not backup_path.exists():
    #        return False

    #    self.create_backup()

    #    self.db.close()

    #    shutil.copy2(backup_path, self.config.db_path)

    #    return True

    # -------------------------
    # INTEGRITY CHECK
    # -------------------------

    def verify_integrity(self) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
            return result == "ok"

    # -------------------------
    # EXPORT CSV
    # -------------------------

    def export_to_csv(self) -> Path:
        """Exports students and movements to CSV files."""
        export_dir = self.config.db_export_dir
        export_dir.mkdir(parents=True, exist_ok=True)

        students_file = export_dir / "students.csv"
        movements_file = export_dir / "movements.csv"

        with self.db.transaction() as conn:
            # Export Students
            students = conn.execute("SELECT * FROM students").fetchall()
            headers_students = [
                desc[0] for desc in conn.execute("SELECT * FROM students").description
            ]

            with open(students_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers_students)
                writer.writerows(students)

            # Export Movements
            movements = conn.execute("SELECT * FROM movements").fetchall()
            headers_movements = [
                desc[0] for desc in conn.execute("SELECT * FROM movements").description
            ]

            with open(movements_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers_movements)
                writer.writerows(movements)

        return export_dir

    # Helpers
    def _cleanup_old_backups(self, keep_last: int = 10):
        backups = sorted(
            self.config.db_backup_dir.glob("student_management_*.db"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for old in backups[keep_last:]:
            old.unlink()
