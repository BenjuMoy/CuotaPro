from domain.accounting.repository import MovementRepository
from domain.student.repository import StudentRepository
from infrastructure.database.connection import DatabaseManager


class UnitOfWork:
    def __init__(self, db: DatabaseManager):
        self._db = db
        self.conn = None

        self.students = None
        self.movements = None

    def __enter__(self):
        self.conn = self._db.connect()

        self.students = StudentRepository(self.conn)
        self.movements = MovementRepository(self.conn)

        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()

        # prevent accidental reuse after exit
        self.conn = None
        self.students = None
        self.movements = None
