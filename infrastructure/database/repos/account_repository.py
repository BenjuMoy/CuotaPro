from collections import defaultdict
from sqlite3 import Connection

from domain.account.model import Account
from domain.accounting.model import Movement
from domain.student.model import Student
from infrastructure.database.repos.movement_repository import MovementRepository
from infrastructure.database.repos.student_repository import StudentRepository


class AccountRepository:
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
        self, students: list[Student], movements: list[Movement]
    ) -> list[Account]:
        movements_by_student: dict[int, list[Movement]] = defaultdict(list)

        for m in movements:
            movements_by_student[m.student_id].append(m)

        return [Account(s, movements_by_student.get(s.id, [])) for s in students]

    # -- Commands

    def save(self, account: Account) -> None:
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
        if not self.conn.in_transaction:
            raise RuntimeError(
                "AccountRepository.save must be used inside a transaction"
            )
        # Persist student changes
        self.students.update(account.student)

        # Persist new movements only
        movements = [m for m in account.movements if m.id is None]

        for m in movements:
            m.id = self.movements.add(m)

    # -- Queries

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
