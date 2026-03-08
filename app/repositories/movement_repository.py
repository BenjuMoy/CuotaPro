import sqlite3
from datetime import datetime
from sqlite3.dbapi2 import Connection

from app.database.connection import DatabaseManager
from app.models.exceptions import BusinessRuleError, NotFound
from app.models.models import Movement

MOVEMENT_COLUMNS = "id, student_id, reference_id, type, amount, month, year, created_at"

EFFECTIVE_MOVEMENT_FILTER = """
m.reference_id IS NULL
AND r.id IS NULL
"""

# IMPORTANT:
# Movements are immutable.
# Do not implement UPDATE or DELETE.


class MovementRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    @staticmethod
    def _row_to_movement(row: sqlite3.Row) -> Movement:
        return Movement.model_validate(dict(row))

    def add(self, movement: Movement, conn: Connection) -> Movement:
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
        RETURNING id, created_at
        """

        cursor = conn.execute(
            query,
            (
                movement.student_id,
                movement.reference_id,
                movement.type,
                movement.amount,
                movement.month,
                movement.year,
            ),
        )
        row = cursor.fetchone()
        movement_id = row["id"]
        created_at = datetime.fromisoformat(row["created_at"])
        return movement.model_copy(update={"id": movement_id, "created_at": created_at})

    # Getters

    def get_all(self, conn: Connection) -> list[Movement]:
        query = f"""
        SELECT {MOVEMENT_COLUMNS}
        FROM movements
        ORDER BY year DESC, month DESC, id DESC
        """

        cursor = conn.execute(query)
        return [self._row_to_movement(row) for row in cursor.fetchall()]

    def get_effective_payments(self, conn: Connection) -> list[Movement]:
        query = f"""SELECT m.*
        FROM movements m
        LEFT JOIN movements r
            ON r.reference_id = m.id
        WHERE {EFFECTIVE_MOVEMENT_FILTER}
        AND m.type = 'PAYMENT'
        ORDER BY m.year DESC, m.month DESC, m.id DESC"""
        cursor = conn.execute(query)
        return [self._row_to_movement(row) for row in cursor.fetchall()]

    def get_effective_fees(self, conn: Connection) -> list[Movement]:
        query = f"""SELECT m.*
        FROM movements m
        LEFT JOIN movements r
            ON r.reference_id = m.id
        WHERE {EFFECTIVE_MOVEMENT_FILTER}
        AND m.type = 'FEE'
        ORDER BY m.year DESC, m.month DESC, m.id DESC"""
        cursor = conn.execute(query)
        return [self._row_to_movement(row) for row in cursor.fetchall()]

    def get_effective_movements_by_id(
        self, student_id: int, conn: Connection
    ) -> list[Movement]:
        query = f"""SELECT m.*
        FROM movements m
        LEFT JOIN movements r
            ON r.reference_id = m.id
        WHERE {EFFECTIVE_MOVEMENT_FILTER}
        AND m.student_id = ?
        ORDER BY m.year DESC, m.month DESC, m.id DESC"""
        cursor = conn.execute(query, (student_id,))
        return [self._row_to_movement(row) for row in cursor.fetchall()]

    def get_by_id(self, movement_id: int, conn: Connection) -> Movement:
        query = f"SELECT {MOVEMENT_COLUMNS} FROM movements WHERE id = ?"
        cursor = conn.execute(query, (movement_id,))
        row = cursor.fetchone()
        if not row:
            raise NotFound("Record not found")
        return self._row_to_movement(row)

    def get_balance(self, student_id: int, conn: Connection) -> int:
        query = f"""SELECT COALESCE(SUM(m.amount), 0)
        FROM movements m
        LEFT JOIN movements r ON r.reference_id = m.id
        WHERE {EFFECTIVE_MOVEMENT_FILTER}
        AND m.student_id = ?"""
        cursor = conn.execute(query, (student_id,))
        return cursor.fetchone()[0]

    def get_student_movements(
        self, student_id: int, conn: Connection
    ) -> list[Movement]:
        query = f"""
            SELECT {MOVEMENT_COLUMNS}
            FROM movements
            WHERE student_id = ?
            ORDER BY year DESC, month DESC, id DESC"""
        cursor = conn.execute(query, (student_id,))

        return [self._row_to_movement(row) for row in cursor.fetchall()]

    def get_student_last_payment(
        self, student_id: int, conn: Connection
    ) -> Movement | None:
        query = f"""
            SELECT m.* FROM movements m
            LEFT JOIN movements r ON r.reference_id = m.id
            WHERE {EFFECTIVE_MOVEMENT_FILTER}
            AND m.student_id = ? AND m.type = 'PAYMENT'
            ORDER BY m.year DESC, m.month DESC, m.id DESC
            LIMIT 1"""
        cursor = conn.execute(query, (student_id,))
        row = cursor.fetchone()
        return self._row_to_movement(row) if row else None

    def get_last_date_applied_fee(self, conn: Connection) -> tuple[int, int] | None:
        """Returns a tuple with the month and the year of the last applied fee, if no date returns None."""
        query = "SELECT month, year FROM movements WHERE type = 'FEE' ORDER BY year DESC, month DESC, id DESC LIMIT 1"
        cursor = conn.execute(query)
        row = cursor.fetchone()
        return (row["month"], row["year"]) if row else None

    def fees_not_applied_for_period(
        self, month: int, year: int, conn: Connection
    ) -> bool:
        query = (
            "SELECT 1 FROM movements WHERE type='FEE' AND month=? AND year=? LIMIT 1"
        )
        return conn.execute(query, (month, year)).fetchone() is None

    def get_month_balance(
        self, student_id: int, month: int, year: int, conn: Connection
    ) -> int:
        """"""
        query = f"""
        SELECT COALESCE(SUM(m.amount),0)
        FROM movements m
        LEFT JOIN movements r ON r.reference_id = m.id
        WHERE {EFFECTIVE_MOVEMENT_FILTER}
        AND m.student_id=? AND m.month=? AND m.year=?"""
        cursor = conn.execute(query, (student_id, month, year))
        return cursor.fetchone()[0]

    def check_not_reversed(self, id: int, conn: Connection):
        existing_reversal = conn.execute(
            "SELECT id FROM movements WHERE reference_id=? AND type='REVERSED'",
            (id,),
        ).fetchone()

        if existing_reversal:
            raise BusinessRuleError("Movimiento ya revertido")

    def get_general_month_balance(
        self, student_id: int, conn: Connection
    ) -> list[tuple[int, int, int]]:
        """Returns in format (month, year, sum)"""
        query = """
        SELECT month, year, SUM(amount) AS total
        FROM movements
        WHERE student_id=?
        GROUP BY year, month"""
        cursor = conn.execute(query, (student_id,))
        return [(row["month"], row["year"], row["total"]) for row in cursor]
