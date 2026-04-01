def test_unique_fee_constraint(movement_repo, student_repo):
    student = student_repo.add(
        student_repo._row_to_student(
            {
                "id": None,
                "active": True,
                "last_name": "Test",
                "first_name": "User",
                "phone1": "123",
                "phone2": "",
                "phone3": "",
                "teacher": "A",
                "book": "",
                "course": "",
                "school": "",
                "year": "",
                "monthly_fee": 10000,
            }
        )
    )

    data = [
        (student.id, None, "FEE", -10000, 1, 2025),
        (student.id, None, "FEE", -10000, 1, 2025),
    ]

    try:
        movement_repo.apply_fees(data)
        assert False, "Should fail due to unique constraint"
    except Exception:
        assert True
