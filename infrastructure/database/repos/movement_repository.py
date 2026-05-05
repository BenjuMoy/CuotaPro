from sqlite3 import Connection, Cursor

from domain.accounting.model import Movement
from domain.accounting.values import Period
from domain.shared.exceptions import NotFound
from infrastructure.database.mappers import row_to_movement

MOVEMENT_COLUMNS = "id, student_id, reference_id, type, amount, month, year, created_at"
ORDER_BY_MOVEMENT_DESC = "ORDER BY year DESC, month DESC, id DESC"


class MovementRepository:
    """
    Repository for Movement entities.

    Constraints:
    - Movements are immutable after creation
    - Only insertion is supported
    - Ordering is always descending by (year, month, id)
    """

    def __init__(self, conn: Connection):
        self.conn = conn

    # --- Helpers --- #

    def _fetch_all(self, cursor: Cursor) -> list[Movement]:
        return [row_to_movement(row) for row in cursor.fetchall()]

    # --- Queries --- #

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
