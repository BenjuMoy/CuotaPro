from app.database.connection import DatabaseManager


def test_fee_persisted(db: DatabaseManager):
    from app.models.models import Movement, MovementType, Student
    from app.repositories.movement_repository import MovementRepository
    from app.repositories.student_repository import StudentRepository

    mov_repo = MovementRepository(db)
    stu_repo = StudentRepository(db)

    student = Student(
        first_name="Tomas",
        last_name="Gonzales",
        phone1="123",
        teacher="Gabriela",
        monthly_fee=100,
    )

    with mov_repo.db_manager.transaction() as conn:
        student = stu_repo.add(student, conn)

        movement = Movement(
            student_id=student.id,
            type=MovementType.FEE,
            amount=-100,
            month=3,
            year=2026,
        )

        movement = mov_repo.add(movement, conn)

        movement = mov_repo.get_by_id(movement.id, conn)

    assert movement.id == student.id
    assert movement.type == MovementType.FEE,
    assert movement.amount == -100
    assert movement.month == 3
    assert movement.year == 2026
