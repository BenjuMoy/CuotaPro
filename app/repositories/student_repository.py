import sqlite3

from app.database.connection import DatabaseManager
from app.models.exceptions import NotFound
from app.models.models import Student

STUDENT_COLUMNS = "id, active, last_name, first_name, phone1, phone2, phone3, teacher, book, course, school, year, monthly_fee"

BASE_SELECT = f"SELECT {STUDENT_COLUMNS} FROM students"

ORDER_BY_STUDENT = "ORDER BY last_name, first_name"

ACTIVE_FILTER = "active = 1"


class StudentRepository:
    """Data Access Object for student operations."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # --- Helper Methods --- #

    @staticmethod
    def _row_to_student(row: sqlite3.Row) -> Student:
        """Converts a database row tuple into a Student Pydantic model."""
        return Student.model_construct(**dict(row), strict=False)

    @staticmethod
    def _student_to_tuple(student: Student):
        return (
            student.active,
            student.last_name,
            student.first_name,
            student.phone1,
            student.phone2,
            student.phone3,
            student.teacher,
            student.book,
            student.course,
            student.school,
            student.year,
            student.monthly_fee,
        )

    def _fetch_all(self, cursor: sqlite3.Cursor) -> list[Student]:
        return [self._row_to_student(row) for row in cursor.fetchall()]

    # --- CRUD Operations --- #

    def add(self, student: Student) -> Student:
        """Add a new student to the database."""
        query = """
        INSERT INTO students (
            active,
            last_name,
            first_name,
            phone1,
            phone2,
            phone3,
            teacher,
            book,
            course,
            school,
            year,
            monthly_fee
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

        with self.db.transaction() as conn:
            cursor = conn.execute(query, (self._student_to_tuple(student)))

            # Get the new ID
            student_id = cursor.lastrowid

        return student.model_copy(update={"id": student_id})

    def update(self, student: Student) -> Student:
        """Update an existing student in the database."""
        if student.id is None:
            raise ValueError("Cannot update without ID")
        query = """
                UPDATE students
                SET active=?, last_name=?, first_name=?, phone1=?, phone2=?, phone3=?, teacher=?, book=?, course=?, school=?, year=?, monthly_fee=?
                WHERE id=?
            """

        with self.db.transaction() as conn:
            cursor = conn.execute(query, (*self._student_to_tuple(student), student.id))

            if cursor.rowcount == 0:
                raise NotFound(f"Student with id {student.id} not found")

        return student

    def update_active_state(self, student_id: int, new_state: bool) -> None:
        """Updates the students state by id"""
        query = "UPDATE students SET active=? WHERE id=?"

        with self.db.transaction() as conn:
            cursor = conn.execute(query, (int(new_state), student_id))

            if cursor.rowcount == 0:
                raise NotFound(f"Student with id {student_id} could not be activated")

    def increase_fees_for_amount(self, old_fee: int, new_fee: int) -> int:
        """Increases the fee for all students whose current fee matches `old_fee` in a single query."""
        query = f"""
            UPDATE students
            SET monthly_fee = ?
            WHERE monthly_fee = ? AND {ACTIVE_FILTER}
        """

        with self.db.transaction() as conn:
            cursor = conn.execute(query, (new_fee, old_fee))
            return cursor.rowcount

    # --- Search methods --- #
    def search_by_name(self, search_term: str) -> list[Student]:
        """Search students by name or partial name."""
        search_pattern = f"%{search_term}%"
        query = f"""
            {BASE_SELECT}
            WHERE last_name LIKE ? COLLATE NOCASE
               OR first_name LIKE ? COLLATE NOCASE
               OR last_name || ' ' || first_name LIKE ? COLLATE NOCASE
               OR first_name || ' ' || last_name LIKE ? COLLATE NOCASE
        """

        with self.db.read() as conn:
            cursor = conn.execute(
                query, (search_pattern, search_pattern, search_pattern, search_pattern)
            )

            return self._fetch_all(cursor)

    def search_by_teacher(self, teacher_name: str) -> list[Student]:
        """Search students by teacher name."""
        search_pattern = f"%{teacher_name}%"
        query = f"""
            {BASE_SELECT}
            WHERE teacher LIKE ? COLLATE NOCASE
            {ORDER_BY_STUDENT}"""

        with self.db.read() as conn:
            cursor = conn.execute(query, (search_pattern,))
            return self._fetch_all(cursor)

    # --- Getters --- #

    def get_all(self) -> list[Student]:
        """Retrieve all students from the database."""
        query = f"""
            {BASE_SELECT}
            {ORDER_BY_STUDENT}
        """

        with self.db.read() as conn:
            cursor = conn.execute(query)
            return self._fetch_all(cursor)

    def get_by_id(self, student_id: int) -> Student:
        """Retrieve a specific student by ID efficiently."""
        query = f"""
            {BASE_SELECT}
            WHERE id=? 
            LIMIT 1
        """

        with self.db.read() as conn:
            cursor = conn.execute(query, (student_id,))
            row = cursor.fetchone()

        if not row:
            raise NotFound(f"Student with id {student_id} not found")

        return self._row_to_student(row)

    def get_debtors(self) -> list[Student]:
        """Gets all students with balance < 0"""
        query = """
        SELECT s.*
        FROM students s
        JOIN (
            SELECT student_id, SUM(amount) AS balance
            FROM movements
            GROUP BY student_id
        ) b ON b.student_id = s.id
        WHERE b.balance < 0"""

        with self.db.read() as conn:
            cursor = conn.execute(query)
            return self._fetch_all(cursor)

    def get_active_student_count(self) -> int:
        """Gets the amount of active students."""
        query = f"SELECT COUNT(*) AS count FROM students WHERE {ACTIVE_FILTER}"

        with self.db.read() as conn:
            cursor = conn.execute(query)
            return cursor.fetchone()["count"]

    def get_all_active_students(self) -> list[Student]:
        query = f"""
            {BASE_SELECT}
            WHERE {ACTIVE_FILTER}
            {ORDER_BY_STUDENT}
        """

        with self.db.read() as conn:
            cursor = conn.execute(query)
            return self._fetch_all(cursor)

    def get_students_without_fee(self, month: int, year: int) -> list[Student]:
        query = f"""
        SELECT s.*
            FROM students s
            WHERE s.{ACTIVE_FILTER}
            AND NOT EXISTS (
        SELECT 1
        FROM movements m
        WHERE m.student_id = s.id
        AND m.type = 'FEE'
        AND m.month = ?
        AND m.year = ?
        )
        """

        with self.db.read() as conn:
            cursor = conn.execute(query, (month, year))
            return self._fetch_all(cursor)

    def count_students_by_monthly_fee(self, monthly_fee: int) -> int:
        """Returns the sum of students with that monthly_fee"""
        query = f"""
            SELECT COUNT(*) AS count
            FROM students
            WHERE monthly_fee = ? AND {ACTIVE_FILTER}
        """

        with self.db.read() as conn:
            cursor = conn.execute(query, (monthly_fee,))
            return cursor.fetchone()["count"]

    def get_fees_list(self) -> list[tuple[int, int]]:
        """Return the count of students by monthly_fee.

        Args:
            conn (Connection): Connection

        Returns:
            list[tuple[int, int]]: The fee count list in format (monthly_fee, count)
        """
        query = (
            "SELECT monthly_fee, COUNT(*) AS count FROM students GROUP BY monthly_fee;"
        )

        with self.db.read() as conn:
            cursor = conn.execute(query)
            return [(row[0], row["count"]) for row in cursor.fetchall()]
