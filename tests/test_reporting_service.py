def test_kpi_metrics(reporting_service, student_service, accounting_service):
    student = student_service.add(
        {
            "last_name": "Diaz",
            "first_name": "Luis",
            "phone1": "123",
            "teacher": "Gomez",
            "monthly_fee": 10000,
        }
    )

    accounting_service.add_fee(1, 2025)

    metrics = reporting_service.get_kpi_metrics()

    assert metrics.active_students == 1
    assert metrics.expected_income == 10000
