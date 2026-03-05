import pytest

from app.services.service_container import ServiceContainer


def test_cannot_pay_already_paid_fee(services: ServiceContainer):
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
    services.accounting.add_payment(student.id, 3, 2026, 100)

    with pytest.raises(Exception):
        services.accounting.add_payment(student.id, 3, 2026, 100)
