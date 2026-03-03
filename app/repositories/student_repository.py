import sqlite3
from sqlite3.dbapi2 import Connection

from app.database.connection import DatabaseManager
from app.models.exceptions import NotFound
from app.models.models import Student

STUDENT_COLUMNS = "id, active, last_name, first_name, phone1, phone2, phone3, teacher, book, course, school, year, monthly_fee"


class StudentRepository:
    """Data Access Object for student operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    # --- Helper Methods --- #

    @staticmethod
    def _row_to_student(row: sqlite3.Row) -> Student:
        """Converts a database row tuple into a Student Pydantic model."""
        return Student.model_validate(dict(row))
        # return Student(**row)

    # --- CRUD Operations --- #

    def add(self, student: Student, conn: Connection) -> Student:
        """Add a new student to the database."""
        query = """
        INSERT INTO students (active, last_name, first_name, phone1, phone2, phone3, teacher, book, course, school, year, monthly_fee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?)
    """

        cursor = conn.execute(
            query,
            (
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
            ),
        )

        # Get the new ID
        student_id = cursor.lastrowid

        return student.model_copy(update={"id": student_id})

    def update(self, student: Student, conn: Connection) -> Student:
        """Update an existing student in the database."""
        if student.id is None:
            raise ValueError("Cannot update without ID")
        query = """
                UPDATE students
                SET active=?, last_name=?, first_name=?, phone1=?, phone2=?, phone3=?, teacher=?, book=?, course=?, school=?, year=?, monthly_fee=?
                WHERE id=?
            """

        cursor = conn.execute(
            query,
            (
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
                student.id,
            ),
        )

        if cursor.rowcount == 0:
            raise NotFound(f"Student with id {student.id} not found")

        return student

    def update_active_state(
        self, student_id: int, new_state: bool, conn: Connection
    ) -> None:
        """Updates the students state by id"""
        query = "UPDATE students SET active=? WHERE id=?"
        cursor = conn.execute(query, (int(new_state), student_id))

        if cursor.rowcount == 0:
            raise NotFound(f"Student with id {student_id} could not be activated")

    def increase_fees_for_amount(
        self, old_fee: int, new_fee: int, conn: Connection
    ) -> int:
        """Increases the fee for all students whose current fee matches `old_fee` in a single query."""
        query = """
            UPDATE students
            SET monthly_fee = ?
            WHERE monthly_fee = ? AND active = 1
        """

        cursor = conn.execute(query, (new_fee, old_fee))
        students_updated = cursor.rowcount
        return students_updated

    # --- Search methods --- #
    def search_by_name(self, search_term: str, conn: Connection) -> list[Student]:
        """Search students by name or partial name."""
        search_pattern = f"%{search_term}%"
        query = f"""
            SELECT {STUDENT_COLUMNS}
            FROM students
            WHERE last_name LIKE ? COLLATE NOCASE
               OR first_name LIKE ? COLLATE NOCASE
               OR last_name || ' ' || first_name LIKE ? COLLATE NOCASE
               OR first_name || ' ' || last_name LIKE ? COLLATE NOCASE
        """

        cursor = conn.execute(
            query, (search_pattern, search_pattern, search_pattern, search_pattern)
        )

        return [self._row_to_student(row) for row in cursor.fetchall()]

    def search_by_teacher(self, teacher_name: str, conn: Connection) -> list[Student]:
        """Search students by teacher name."""
        search_pattern = f"%{teacher_name}%"
        query = f"""
            SELECT e.{STUDENT_COLUMNS}
            FROM students e
            WHERE LOWER(e.teacher) LIKE LOWER(?)
            ORDER BY e.last_name, e.first_name"""
        cursor = conn.execute(query, (search_pattern,))
        return [self._row_to_student(row) for row in cursor.fetchall()]

    # --- Getters --- #

    def get_all(self, conn: Connection) -> list[Student]:
        """Retrieve all students from the database."""
        query = f"""
            SELECT e.{STUDENT_COLUMNS}
            FROM students e
            ORDER BY e.last_name, e.first_name
        """
        cursor = conn.execute(query)
        return [self._row_to_student(row) for row in cursor.fetchall()]

    def get_by_id(self, student_id: int, conn: Connection) -> Student:
        """Retrieve a specific student by ID efficiently."""
        query = f"""
            SELECT e.{STUDENT_COLUMNS}
            FROM students e
            WHERE e.id=?
        """
        cursor = conn.execute(query, (student_id,))
        row = cursor.fetchone()
        if not row:
            raise NotFound(f"Student with id {student_id} not found")

        return self._row_to_student(row)

    def get_debtors(self, conn: Connection) -> list[Student]:
        """Gets all students with balance < 0"""
        query = f"""
        SELECT e.{STUDENT_COLUMNS}
        FROM students e
        WHERE e.active = 1
        AND (SELECT COALESCE(SUM(m.amount), 0)
             FROM movements m
             WHERE m.student_id = e.id) < 0;"""

        cursor = conn.execute(query)
        return [self._row_to_student(row) for row in cursor.fetchall()]

    def get_active_student_count(self, conn: Connection) -> int:
        """Gets the amount of active students."""
        query = "SELECT COUNT(*) FROM students WHERE active = 1"
        cursor = conn.execute(query)
        return cursor.fetchone()[0]

    def get_all_active_students(self, conn: Connection) -> list[Student]:
        query = f"""
        SELECT {STUDENT_COLUMNS}
        FROM students WHERE active = 1
        ORDER BY last_name, first_name"""
        cursor = conn.execute(query)
        return [self._row_to_student(row) for row in cursor.fetchall()]

    def count_students_by_monthly_fee(self, monthly_fee: int, conn: Connection) -> int:
        """Returns the sum of students with that monthly_fee"""
        query = """
        SELECT COUNT(*)
        FROM students
        WHERE monthly_fee = ?"""

        cursor = conn.execute(
            query,
            (monthly_fee,),
        )

        return cursor.fetchone()[0]

    def get_fees_list(self, conn: Connection) -> list[tuple[int, int]]:
        query = (
            "SELECT monthly_fee, COUNT(*) AS count FROM students GROUP BY monthly_fee;"
        )
        cursor = conn.execute(query)
        return [(data[0], data[1]) for data in cursor.fetchall()]
