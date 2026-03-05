from app.services.service_container import ServiceContainer


def test_create_student(services: ServiceContainer):
    student = services.student.add(
        {
            "first_name": "Tomas",
            "last_name": "Gonzales",
            "phone1": "123",
            "teacher": "Gabriela",
            "monthly_fee": 100,
        }
    )

    assert student.id is not None
    assert student.first_name == "Tomas"
    assert student.last_name == "Gonzales"
    assert student.phone1 == "123"
    assert student.teacher == "Gabriela"
    assert student.monthly_fee == 100
