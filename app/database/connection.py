import os
import sqlite3
from contextlib import contextmanager
from sqlite3.dbapi2 import Connection

from app.database.config import DatabaseConfig


class DatabaseManager:
    def __init__(self, db_config: DatabaseConfig):
        self.db_path = db_config.db_path
        self._connection: Connection | None = None
        self.db_config = db_config
        os.makedirs(self.db_config.db_dir, exist_ok=True)

    def connect(self):
        self.db_config.db_backup_dir.mkdir(parents=True, exist_ok=True)
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES,
                check_same_thread=False,
                # detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._connection.row_factory = sqlite3.Row
            self.db_config.apply_pragmas(self._connection)

        return self._connection

    def close(self):
        if self._connection:
            try:
                self._connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass

            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def read(self):
        conn = self.connect()
        try:
            yield conn
        except Exception:
            raise
