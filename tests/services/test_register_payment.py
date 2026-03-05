from app.services.service_container import ServiceContainer


def test_payment_reduces_balance(services: ServiceContainer):
    student = services.student.add(
        {
            "first_name": "Tomas",
            "last_name": "Gonzales",
            "phone1": "123",
            "teacher": "Gabriela",
            "monthly_fee": 100,
        }
    )

    services.accounting.add_fee(3, 2026)
    services.accounting.add_payment(student.id, 3, 2026, 150)

    balance = services.accounting.get_balance_by_id(student.id)

    assert balance == 50
