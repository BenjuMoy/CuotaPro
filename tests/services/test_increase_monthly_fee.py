from app.services.service_container import ServiceContainer


def test_increase_monthly_fee(services: ServiceContainer):
    student = services.student.add(
        {
            "first_name": "Tomas",
            "last_name": "Gonzales",
            "phone1": "123",
            "teacher": "Gabriela",
            "monthly_fee": 100,
        }
    )

    num = services.accounting.increase(100, 200)

    student = services.student.get_by_id(student.id)

    assert num > 0
    assert student.monthly_fee == 200
