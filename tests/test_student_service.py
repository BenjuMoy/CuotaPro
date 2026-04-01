import pytest

from app.models.exceptions import NotFound


def test_add_student(student_service):
    student = student_service.add(
        {
            "last_name": "Perez",
            "first_name": "Juan",
            "phone1": "123",
            "teacher": "Gomez",
            "monthly_fee": 10000,
        }
    )

    assert student.id is not None
    assert student.active is True


def test_update_student(student_service):
    student = student_service.add(
        {
            "last_name": "Perez",
            "first_name": "Juan",
            "phone1": "123",
            "teacher": "Gomez",
            "monthly_fee": 10000,
        }
    )

    updated = student_service.update(student.id, {"monthly_fee": 15000})

    assert updated.monthly_fee == 15000


def test_toggle_active(student_service):
    student = student_service.add(
        {
            "last_name": "Perez",
            "first_name": "Juan",
            "phone1": "123",
            "teacher": "Gomez",
            "monthly_fee": 10000,
        }
    )

    student_service.toggle_active(student.id)
    updated = student_service.get_by_id(student.id)

    assert updated.active is False


def test_get_nonexistent_student(student_service):
    with pytest.raises(NotFound):
        student_service.get_by_id(999)
