from collections import defaultdict
from sqlite3 import Connection

from domain.account.model import Account
from domain.accounting.model import Movement
from domain.shared.exceptions import NotFound
from domain.student.model import StudentProfile
from infrastructure.database.mappers import student_to_params
from infrastructure.database.repos.movement_repository import MovementRepository
from infrastructure.database.repos.student_repository import StudentRepository


class AccountRepository:
    """
    AccountRepository (Write Model)

    Responsibilities:
    - Persist Account aggregate
    - Ensure consistency between Student and Movements

    Rules:
    - This is the ONLY write entry point for the aggregate
    - StudentRepository and MovementRepository are read-only

    Notes:
    - New movements are detected by id=None
    - Student updates are always persisted together with movements
    """

    def __init__(
        self,
        conn: Connection,
        student_repo: StudentRepository,
        movement_repo: MovementRepository,
    ):
        self.conn = conn
        self.students = student_repo
        self.movements = movement_repo

    # --- Helpers --- #

    def _build_accounts(
        self, students: list[StudentProfile], movements: list[Movement]
    ) -> list[Account]:
        movements_by_student: dict[int, list[Movement]] = defaultdict(list)

        for m in movements:
            movements_by_student[m.student_id].append(m)

        return [Account(s, movements_by_student.get(s.id, [])) for s in students]

    def _is_new(self, entity) -> bool:
        return entity.id is None

    # -- Commands

    def _add_student(self, s: StudentProfile) -> int:
        """Persists student and MUTATES its id (identity assignment)."""
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
        cursor = self.conn.execute(query, student_to_params(s))

        if not cursor.lastrowid:
            raise RuntimeError("Failed to insert student")

        s.id = cursor.lastrowid
        return s.id

    def _update_student(self, s: StudentProfile) -> int:
        if s.id is None:
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

        params = student_to_params(s)
        params["id"] = s.id

        cursor = self.conn.execute(query, params)

        if cursor.rowcount == 0:
            raise NotFound(f"Student with id {s.id} not found")

        return s.id

    def _add_movement(self, m: Movement) -> int:
        # SIDE EFFECT: mutates entity identity
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
                m.student_id,
                m.reference_id,
                m.type.value,
                m.amount.amount,
                m.period.month,
                m.period.year,
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError("Failed to insert student")

        row = cursor.fetchone()
        m.created_at = row["created_at"]

        m.id = cursor.lastrowid
        return m.id

    def save(self, account: Account) -> int:
        """
        Persists the Account aggregate.

        Rules:
        - Must be called inside a UnitOfWork transaction
        - Persists:
            - Student updates
            - New movements only (id is None)
        - Does NOT update existing movements (immutable)

        Side effects:
        - Assigns IDs to new movements
        """
        # Persist student changes
        if account.student.id is None:
            student_id = self._add_student(account.student)
        else:
            self._update_student(account.student)

        # Persist new movements only
        movements = [m for m in account.movements if m.id is None]

        for m in movements:
            m.student_id = account.student.id
            m.id = self._add_movement(m)

        return account.student.id

    # --- Queries

    def get(self, student_id: int) -> Account:
        student = self.students.get_by_id(student_id)
        movements = self.movements.list_by_student_id(student_id)
        return Account(student, movements)

    def get_many(self, student_ids: list[int]) -> list[Account]:
        if not student_ids:
            return []

        students = self.students.list_by_ids(student_ids)
        movements = self.movements.list_by_students_ids(student_ids)

        return self._build_accounts(students, movements)

    def list_active_accounts(self) -> list[Account]:
        students = self.students.list_active()
        movements = self.movements.list_by_students_ids([s.id for s in students])

        return self._build_accounts(students, movements)
