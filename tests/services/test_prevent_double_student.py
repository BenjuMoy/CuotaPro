import pytest

from app.services.service_container import ServiceContainer


def test_create_student(services: ServiceContainer):
    student1 = {
        "first_name": "Tomas",
        "last_name": "Gonzales",
        "phone1": "123",
        "teacher": "Gabriela",
        "monthly_fee": 100,
    }

    services.student.add(student1)

    student2 = {
        "first_name": "benju",
        "last_name": "Gonzales",
        "phone1": "123",
        "teacher": "Gabriela",
        "monthly_fee": 100,
    }

    with pytest.raises(Exception):
        services.student.add(student1)

    services.student.add(student2)
