from sqlite3 import Cursor, Row

from domain.shared.exceptions import NotFound
from domain.student.model import Student
from domain.student.values import MonthlyFee, PhoneNumber, StudentName
from infrastructure.database.unit_of_work import UnitOfWork

STUDENT_COLUMNS = "id, active, last_name, first_name, phone1, phone2, phone3, teacher, book, course, school, year, monthly_fee"
BASE_SELECT = f"SELECT {STUDENT_COLUMNS} FROM students"
ORDER_BY_STUDENT = "ORDER BY last_name, first_name"
ACTIVE_FILTER = "active = 1"


class StudentRepository:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    @staticmethod
    def row_to_student(row: Row) -> Student:
        return Student(
            id=row["id"],
            active=bool(row["active"]),
            name=StudentName(
                first_name=row["first_name"],
                last_name=row["last_name"],
            ),
            phone1=PhoneNumber(row["phone1"]),
            phone2=PhoneNumber(row["phone2"]) if row["phone2"] else None,
            phone3=PhoneNumber(row["phone3"]) if row["phone3"] else None,
            teacher=row["teacher"],
            book=row["book"],
            course=row["course"],
            school=row["school"],
            school_year=row["year"],
            monthly_fee=MonthlyFee(row["monthly_fee"]),
        )

    @staticmethod
    def student_to_dict(student: Student) -> dict:
        return {
            "active": int(student.active),
            "last_name": student.name.last_name,
            "first_name": student.name.first_name,
            "phone1": student.phone1.value,
            "phone2": student.phone2.value if student.phone2 else "",
            "phone3": student.phone3.value if student.phone3 else "",
            "teacher": student.teacher,
            "book": student.book,
            "course": student.course,
            "school": student.school,
            "year": student.school_year,
            "monthly_fee": student.monthly_fee.amount,
        }

    def _fetch_all(self, cursor: Cursor) -> list[Student]:
        return [self.row_to_student(row) for row in cursor.fetchall()]

    def add(self, student: Student) -> Student:
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
            VALUES (
                :active, :last_name, :first_name, :phone1,
                :phone2, :phone3, :teacher, :book,
                :course, :school, :year, :monthly_fee
            )
        """
        cursor = self.uow.conn.execute(query, self.student_to_dict(student))

        student.id = cursor.lastrowid
        return student

    def update(self, student: Student) -> Student:
        if student.id is None:
            raise ValueError("Cannot update without ID")

        query = """
        UPDATE students
        SET
            active=:active,
            last_name=:last_name,
            first_name=:first_name,
            phone1=:phone1,
            phone2=:phone2,
            phone3=:phone3,
            teacher=:teacher,
            book=:book,
            course=:course,
            school=:school,
            year=:year,
            monthly_fee=:monthly_fee
        WHERE id=:id
        """

        params = self.student_to_dict(student)
        params["id"] = student.id

        cursor = self.uow.conn.execute(query, (params))

        if cursor.rowcount == 0:
            raise NotFound(f"Student with id {student.id} not found")

        return student

    def increase_monthly_fee_batch(self, old_fee: int, new_fee: int) -> int:
        query = "UPDATE students SET monthly_fee = ? WHERE monthly_fee = ?"
        cursor = self.uow.conn.execute(query, (new_fee, old_fee))
        return cursor.rowcount

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

        cursor = self.uow.conn.execute(query, params)
        return self._fetch_all(cursor)

    def get_all(self) -> list[Student]:
        query = f"""
            {BASE_SELECT}
            {ORDER_BY_STUDENT}
        """
        cursor = self.uow.conn.execute(query)
        return self._fetch_all(cursor)

    def get_by_id(self, student_id: int) -> Student:
        query = f"""
            {BASE_SELECT}
            WHERE id=?
            LIMIT 1
        """
        cursor = self.uow.conn.execute(query, (student_id,))
        row = cursor.fetchone()

        if not row:
            raise NotFound(f"Student with id {student_id} not found")

        return self.row_to_student(row)

    def list_by_ids(self, ids: list[int]) -> list[Student]:
        if not ids:
            return []

        placeholders = ",".join("?" for _ in ids)
        query = f"{BASE_SELECT} WHERE id IN ({placeholders}) {ORDER_BY_STUDENT}"

        cursor = self.uow.conn.execute(query, ids)
        return self._fetch_all(cursor)

    def count_active(self) -> int:
        query = f"SELECT COUNT(*) AS count FROM students WHERE {ACTIVE_FILTER}"
        cursor = self.uow.conn.execute(query)
        return cursor.fetchone()["count"]

    def list_active(self) -> list[Student]:
        query = f"""
            {BASE_SELECT}
            WHERE {ACTIVE_FILTER}
            {ORDER_BY_STUDENT}
        """
        cursor = self.uow.conn.execute(query)
        return self._fetch_all(cursor)

    def count_by_monthly_fee(self, monthly_fee: int) -> int:
        query = f"""
            SELECT COUNT(*) AS count
            FROM students
            WHERE monthly_fee = ? AND {ACTIVE_FILTER}
        """
        cursor = self.uow.conn.execute(query, (monthly_fee,))
        return cursor.fetchone()["count"]

    def get_fees_list(self) -> list[tuple[int, int]]:
        query = """
            SELECT monthly_fee, COUNT(*) AS count
            FROM students
            GROUP BY monthly_fee
        """
        cursor = self.uow.conn.execute(query)
        return [(row[0], row["count"]) for row in cursor.fetchall()]
