import csv
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

from infrastructure.config.database_config import DatabaseConfig
from infrastructure.database.connection import DatabaseManager


logger = logging.getLogger()


class MaintenanceService:
    def __init__(self, db_manager: DatabaseManager, paths: DatabaseConfig):
        self.db = db_manager
        self.config = paths

    # -------------------------
    # BACKUP
    # -------------------------

    def create_backup(self) -> Path:
        """
        Creates a safe SQLite backup using the online backup API.
        This method is safe to run while the application is in use.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"student_management_{timestamp}.db"
        backup_path = self.config.backup_dir / backup_name

        self.config.backup_dir.mkdir(parents=True, exist_ok=True)

        # For backup, we need a direct, long-lived connection to the source database.
        # We bypass the transaction() context manager here.
        source_conn = sqlite3.connect(self.config.database_path)
        source_conn.execute("PRAGMA wal_checkpoint(FULL);")  # Flush WAL to main DB file

        try:
            # The destination connection is also a direct connection to the new file.
            dest_conn = sqlite3.connect(backup_path)
            try:
                # The backup() method copies the database over.
                source_conn.backup(dest_conn)
            finally:
                dest_conn.close()
        finally:
            source_conn.close()

        # Clean up old backups after a successful new one is created.
        self._cleanup_old_backups()
        return backup_path

    # -------------------------
    # List BackUps
    # -------------------------

    def list_backup_files(self) -> List[Path]:
        """Lists all backup files, sorted by modification time (newest first)."""
        if not self.config.backup_dir.exists():
            return []

        backup_files = list(self.config.backup_dir.glob("student_management_*.db"))
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return backup_files

    # -------------------------
    # RESTORE
    # -------------------------

    def restore_backup(self, file_path: Path) -> bool:
        """
        Restores the database from a backup file.
        WARNING: This is a destructive operation.
        """
        backup_path = Path(file_path)

        if not backup_path.is_file():
            # Log this event
            logger.error(f"Restore failed: Backup file not found at {backup_path}")
            return False

        # Safety backup before restore
        logger.info("Creating a safety backup before restoring...")
        self.create_backup()

        # Close all existing connections managed by the DatabaseManager if possible.
        # This is crucial to prevent locked database errors.
        # Your DatabaseManager would need a method for this.
        # For this example, we assume we can get a fresh connection.

        try:
            # Source is the backup file, destination is the main database file.
            source_conn = sqlite3.connect(backup_path)
            dest_conn = sqlite3.connect(self.config.database_path)
            try:
                source_conn.backup(dest_conn)
                logger.info(f"Successfully restored database from {backup_path}")
                return True
            finally:
                source_conn.close()
                dest_conn.close()
        except Exception as e:
            # Log this error
            logger.exception(f"Restore failed: {e}")
            return False

    # -------------------------
    # INTEGRITY CHECK
    # -------------------------

    def verify_integrity(self) -> bool:
        """Performs a full integrity check on the database."""
        # This is a read-only operation, so using the transaction manager is fine.
        with self.db.read() as conn:
            cursor = conn.execute("PRAGMA integrity_check;")
            # The result is a one-row table with "ok" if everything is fine.
            result = cursor.fetchone()[0]
            return result == "ok"

    # -------------------------
    # EXPORT CSV
    # -------------------------

    def export_to_csv(self) -> Path:
        """Exports students and movements to CSV files."""
        export_dir = self.config.export_dir
        export_dir.mkdir(parents=True, exist_ok=True)

        students_file = export_dir / "students.csv"
        movements_file = export_dir / "movements.csv"

        with self.db.read() as conn:
            # --- Export Students ---
            cursor = conn.execute("SELECT * FROM students")
            students = cursor.fetchall()
            headers_students = [desc[0] for desc in cursor.description]

            with open(students_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers_students)
                writer.writerows(students)

            # --- Export Movements ---
            cursor = conn.execute("SELECT * FROM movements")
            movements = cursor.fetchall()
            headers_movements = [desc[0] for desc in cursor.description]

            with open(movements_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers_movements)
                writer.writerows(movements)

        return export_dir

    # -------------------------
    # Helper
    # -------------------------

    def _cleanup_old_backups(self, keep_last: int = 10):
        """Deletes old backups, keeping only the most recent `keep_last`."""
        backups = sorted(
            self.config.backup_dir.glob("student_management_*.db"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[keep_last:]:
            try:
                old_backup.unlink()
            except OSError as e:
                # Log this error but don't let it stop the process
                logger.exception(f"Error deleting old backup {old_backup}: {e}")

    def get_database_stats(self):  # TODO
        ...
