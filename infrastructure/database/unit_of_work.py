from infrastructure.database.connection import DatabaseManager


class UnitOfWork:
    def __init__(self, db: DatabaseManager):
        self._db = db
        self.conn = None

    def __enter__(self):
        self.conn = self._db.connect()
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
