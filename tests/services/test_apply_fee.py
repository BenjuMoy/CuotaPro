from app.services.service_container import ServiceContainer


def test_apply_monthly_fee_creates_debt(services: ServiceContainer):
    student = services.student.add(
        {
            "first_name": "Tomas",
            "last_name": "Gonzales",
            "phone1": "123",
            "teacher": "Gabriela",
            "monthly_fee": 100,
        }
    )

    num = services.accounting.add_fee(3, 2026)

    balance = services.accounting.get_balance_by_id(student.id)

    assert num > 0
    assert balance == -100
