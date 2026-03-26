import sqlite3
from contextlib import contextmanager
from sqlite3 import Connection
from typing import Any, Generator

from app.database.config import DatabaseConfig


class DatabaseManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.config.ensure_directories_exist()

    def connect(self) -> Connection:
        conn = sqlite3.connect(
            self.config.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        self._apply_pragmas(conn)
        return conn

    def _apply_pragmas(self, conn: Connection):
        """Apply pragmas to connection."""
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA wal_autocheckpoint = 1000;")

    @contextmanager
    def transaction(self) -> Generator[Connection, Any, None]:
        """Opens connection to write in db file."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def read(self) -> Generator[Connection, Any, None]:
        """Opens connection to read db file."""
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()
