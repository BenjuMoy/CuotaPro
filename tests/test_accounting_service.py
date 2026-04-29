from datetime import datetime

import pytest

from application.models.exceptions import BusinessRuleError


def create_student(student_service):
    return student_service.add(
        {
            "last_name": "Lopez",
            "first_name": "Ana",
            "phone1": "123",
            "teacher": "Gomez",
            "monthly_fee": 10000,
        }
    )


def test_add_fee(accounting_service, student_service):
    student = create_student(student_service)

    count = accounting_service.add_fee(month=1, year=2025)

    assert count == 1


def test_add_payment(accounting_service, student_service):
    student = create_student(student_service)

    accounting_service.add_fee(month=1, year=2025)

    student, balance, movement = accounting_service.add_payment(
        student.id, 1, 2025, 10000
    )

    assert movement.amount == 10000
    assert balance == 0


def test_payment_without_debt_fails(accounting_service, student_service):
    student = create_student(student_service)

    with pytest.raises(BusinessRuleError):
        accounting_service.add_payment(student.id, 1, 2025, 10000)


def test_future_payment_fails(accounting_service, student_service):
    student = create_student(student_service)

    now = datetime.now()
    future_month = now.month + 1 if now.month < 12 else 1
    future_year = now.year if now.month < 12 else now.year + 1

    with pytest.raises(BusinessRuleError):
        accounting_service.add_payment(student.id, future_month, future_year, 10000)


def test_reverse_payment(accounting_service, student_service):
    student = create_student(student_service)

    accounting_service.add_fee(1, 2025)
    _, _, payment = accounting_service.add_payment(student.id, 1, 2025, 10000)

    reversal = accounting_service.reverse(payment.id)

    assert reversal.reference_id == payment.id
    assert reversal.amount == -payment.amount


def test_double_reverse_fails(accounting_service, student_service):
    student = create_student(student_service)

    accounting_service.add_fee(1, 2025)
    _, _, payment = accounting_service.add_payment(student.id, 1, 2025, 10000)

    accounting_service.reverse(payment.id)

    with pytest.raises(BusinessRuleError):
        accounting_service.reverse(payment.id)
