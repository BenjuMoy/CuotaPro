from sqlite3 import Connection, Cursor

from domain.accounting.model import Movement
from domain.accounting.values import Period
from domain.shared.exceptions import NotFound
from infrastructure.database.mappers import row_to_movement

MOVEMENT_COLUMNS = "id, student_id, reference_id, type, amount, month, year, created_at"
ORDER_BY_MOVEMENT_DESC = "ORDER BY year DESC, month DESC, id DESC"

# Only new movements are supported
# Movements are immutable after creation

# movements must be ordered DESC by date


class MovementRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

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

        cursor = self.conn.execute(
            query,
            (
                movement.student_id,
                movement.reference_id,
                movement.type.value,
                movement.amount.amount,
                movement.period.month,
                movement.period.year,
            ),
        )

        row = cursor.fetchone()
        movement.id = cursor.lastrowid

        movement.created_at = row["created_at"]
        return movement

    def add_many(self, movements: list[Movement]) -> int:
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
        """

        data = [
            (
                m.student_id,
                m.reference_id,
                m.type.value,
                m.amount.amount,
                m.period.month,
                m.period.year,
            )
            for m in movements
        ]

        cursor = self.conn.executemany(query, data)
        return cursor.rowcount

    def get_all(self) -> list[Movement]:
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            {ORDER_BY_MOVEMENT_DESC}
        """
        cursor = self.conn.execute(query)
        return self._fetch_all(cursor)

    def get_by_id(self, movement_id: int) -> Movement:
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            WHERE id = ?
        """
        cursor = self.conn.execute(query, (movement_id,))
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
        cursor = self.conn.execute(query, (student_id,))
        return self._fetch_all(cursor)

    def list_by_students_ids(self, ids: list[int]) -> list[Movement]:
        if not ids:
            return []

        # NOTE Limit is 999
        placeholders = ",".join("?" for _ in ids)
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            WHERE student_id IN ({placeholders})
            {ORDER_BY_MOVEMENT_DESC}
        """
        cursor = self.conn.execute(query, ids)
        return self._fetch_all(cursor)

    def get_last_date_applied_fee(self) -> Period | None:
        query = f"""
            SELECT month, year
            FROM movements
            WHERE type = 'FEE'
            {ORDER_BY_MOVEMENT_DESC}
            LIMIT 1
        """
        cursor = self.conn.execute(query)
        row = cursor.fetchone()

        return Period(row["month"], row["year"]) if row else None
