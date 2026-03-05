from app.services.service_container import ServiceContainer


def test_search_student(services: ServiceContainer):
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


    list1 = services.student.search_by_name(student.first_name)
    list2 = services.student.search_by_teacher(student.teacher)
    list3 = services.student.get_debtors()

    assert list1
    assert list2
    assert list3
