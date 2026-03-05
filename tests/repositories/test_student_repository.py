from app.database.connection import DatabaseManager


def test_student_persisted(db: DatabaseManager):
    from app.repositories.student_repository import StudentRepository
    from app.models.models import Student

    repo = StudentRepository(db)

    student = Student(first_name="Tomas", last_name="Gonzales", phone1="123", teacher="Gabriela", monthly_fee=100)

    with repo.db_manager.transaction() as conn:
        student = repo.add(student, conn)

        student = repo.get_by_id(student.id, conn)

    assert student.first_name == "Tomas"
    assert student.last_name == "Gonzales"
    assert student.phone1 == "123"
    assert student.teacher == "Gabriela"
    assert student.monthly_fee == 100
