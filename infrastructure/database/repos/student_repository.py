from sqlite3 import Connection, Cursor

from domain.shared.exceptions import NotFound
from domain.student.model import Student
from infrastructure.database.mappers import row_to_student

STUDENT_COLUMNS = "id, active, last_name, first_name, phone1, phone2, phone3, teacher, book, course, school, year, monthly_fee"
BASE_SELECT = f"SELECT {STUDENT_COLUMNS} FROM students"
ORDER_BY_STUDENT = "ORDER BY last_name, first_name"
ACTIVE_FILTER = "active = 1"


class StudentRepository:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    # --- helpers --- #

    def _fetch_all(self, cursor: Cursor) -> list[Student]:
        return [row_to_student(row) for row in cursor.fetchall()]

    # --- Queries --- #

    def search_students(
        self,
        name: str | None = None,
        teacher: str | None = None,
        active: bool | None = None,
    ) -> list[Student]:
        conditions = []
        params = []

        if name:
            search_pattern = f"%{name}%"
            conditions.append(
                """(
                    last_name LIKE ? COLLATE NOCASE OR
                    first_name LIKE ? COLLATE NOCASE OR
                    last_name || ' ' || first_name LIKE ? COLLATE NOCASE OR
                    first_name || ' ' || last_name LIKE ? COLLATE NOCASE
                )"""
            )
            params.extend([search_pattern] * 4)

        if teacher:
            conditions.append("teacher LIKE ? COLLATE NOCASE")
            params.append(f"%{teacher}%")

        if active is not None:
            conditions.append("active = ?")
            params.append(1 if active else 0)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            {BASE_SELECT}
            {where_clause}
            {ORDER_BY_STUDENT}
        """

        cursor = self.conn.execute(query, params)
        return self._fetch_all(cursor)

    def get_all(self) -> list[Student]:
        query = f"""
            {BASE_SELECT}
            {ORDER_BY_STUDENT}
        """
        cursor = self.conn.execute(query)
        return self._fetch_all(cursor)

    def get_by_id(self, student_id: int) -> Student:
        query = f"""
            {BASE_SELECT}
            WHERE id=?
            LIMIT 1
        """
        cursor = self.conn.execute(query, (student_id,))
        row = cursor.fetchone()

        if not row:
            raise NotFound(f"Student with id {student_id} not found")

        return row_to_student(row)

    def list_by_ids(self, ids: list[int]) -> list[Student]:
        if not ids:
            return []

        placeholders = ",".join("?" for _ in ids)
        query = f"{BASE_SELECT} WHERE id IN ({placeholders}) {ORDER_BY_STUDENT}"

        cursor = self.conn.execute(query, ids)
        return self._fetch_all(cursor)

    def list_active_ids(self) -> list[int]:
        query = f"""
            SELECT id
            FROM students
            WHERE {ACTIVE_FILTER}
            {ORDER_BY_STUDENT}
        """

        cursor = self.conn.execute(query)
        return [row["id"] for row in cursor.fetchall()]

    def count_active(self) -> int:
        query = f"SELECT COUNT(*) AS count FROM students WHERE {ACTIVE_FILTER}"
        cursor = self.conn.execute(query)
        return cursor.fetchone()["count"]

    def list_active(self) -> list[Student]:
        query = f"""
            {BASE_SELECT}
            WHERE {ACTIVE_FILTER}
            {ORDER_BY_STUDENT}
        """
        cursor = self.conn.execute(query)
        return self._fetch_all(cursor)

    def count_by_monthly_fee(self, monthly_fee: int) -> int:
        query = f"""
            SELECT COUNT(*) AS count
            FROM students
            WHERE monthly_fee = ? AND {ACTIVE_FILTER}
        """
        cursor = self.conn.execute(query, (monthly_fee,))
        return cursor.fetchone()["count"]

    def get_fees_list(self) -> list[tuple[int, int]]:
        query = """
            SELECT monthly_fee, COUNT(*) AS count
            FROM students
            GROUP BY monthly_fee
        """
        cursor = self.conn.execute(query)
        return [(row[0], row["count"]) for row in cursor.fetchall()]
