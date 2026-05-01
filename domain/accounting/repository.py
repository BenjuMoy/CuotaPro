from sqlite3 import Cursor

from domain.accounting.model import Movement
from domain.accounting.values import Period
from domain.shared.exceptions import NotFound
from infrastructure.database.mappers import row_to_movement
from infrastructure.database.unit_of_work import UnitOfWork

MOVEMENT_COLUMNS = "id, student_id, reference_id, type, amount, month, year, created_at"
ORDER_BY_MOVEMENT_DESC = "ORDER BY year DESC, month DESC, id DESC"


class MovementRepository:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _fetch_all(self, cursor: Cursor) -> list[Movement]:
        return [row_to_movement(row) for row in cursor.fetchall()]

    def add(self, movement: Movement) -> Movement:
        query = """
            INSERT INTO movements(
                student_id,
                reference_id,
                type,
                amount,
                month,
                year
            )
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING created_at
        """

        cursor = self.uow.conn.execute(
            query,
            (
                movement.student_id,
                movement.reference_id,
                movement.type,
                movement.amount.amount,
                movement.period.month,
                movement.period.year,
            ),
        )

        row = cursor.fetchone()
        movement.id = cursor.lastrowid

        movement.created_at = row["created_at"]
        return movement

    def apply_fees(self, data: list[tuple]) -> int:
        cursor = self.uow.conn.executemany(
            """
            INSERT INTO movements(
                student_id,
                reference_id,
                type,
                amount,
                month,
                year
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        return cursor.rowcount

    def get_all(self) -> list[Movement]:
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            {ORDER_BY_MOVEMENT_DESC}
        """
        cursor = self.uow.conn.execute(query)
        return self._fetch_all(cursor)

    def get_by_id(self, movement_id: int) -> Movement:
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            WHERE id = ?
        """
        cursor = self.uow.conn.execute(query, (movement_id,))
        row = cursor.fetchone()

        if not row:
            raise NotFound("Record not found")

        return row_to_movement(row)

    def list_by_student_id(self, student_id: int) -> list[Movement]:
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            WHERE student_id = ?
            {ORDER_BY_MOVEMENT_DESC}
        """
        cursor = self.uow.conn.execute(query, (student_id,))
        return self._fetch_all(cursor)

    def list_by_students_ids(self, ids: list[int]) -> list[Movement]:
        if not ids:
            return []

        placeholders = ",".join("?" for _ in ids)
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            WHERE student_id IN ({placeholders})
            {ORDER_BY_MOVEMENT_DESC}
        """
        cursor = self.uow.conn.execute(query, ids)
        return self._fetch_all(cursor)

    def get_last_date_applied_fee(self) -> Period | None:
        query = f"""
            SELECT month, year
            FROM movements
            WHERE type = 'FEE'
            {ORDER_BY_MOVEMENT_DESC}
            LIMIT 1
        """
        cursor = self.uow.conn.execute(query)
        row = cursor.fetchone()

        return Period(row["month"], row["year"]) if row else None
