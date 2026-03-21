import sqlite3
from contextlib import contextmanager
from sqlite3 import Connection

from app.database.config import DatabaseConfig


class DatabaseManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config

    def connect(self) -> Connection:
        conn = sqlite3.connect(
            self.config.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        self.config.apply_pragmas(conn)
        return conn

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
