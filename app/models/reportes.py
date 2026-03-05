from app.models.models import Movement, Student


class SalaryReport:
    def __init__(self, student_list: list[Student]):
        self.student_list: list[Student] = student_list

    def generar_salario_teacher(
        self, professor_name: str
    ) -> dict[str, str | int | list[dict[str, str | int]]]:
        professor_name = professor_name.strip().title()
        details: list[dict[str, str | int]] = []
        total = 0

        for student in self.student_list:
            if student.active and student.teacher == professor_name:
                details.append(
                    {
                        "last_name": student.last_name,
                        "first_name": student.first_name,
                        "monthly_fee": student.monthly_fee,
                    }
                )
                total += student.monthly_fee

        if not details:
            raise ValueError(
                f"No se encontraron estudiantes activos para el profesor: {professor_name}"
            )

        return {
            "teacher": professor_name,
            "total": total,
            "student_count": len(details),
            "details": details,
        }

    def generar_reporte_financiero(
        self,
        student_list: list[Student],
        pagos_list: list[Movement],
        mes: int,
        year: int,
    ):
        """Generate financial report for a specific month"""
        # Get payments for the month
        pagos_mes = [p for p in pagos_list if p.month == mes]

        # Calculate totals
        total_recaudado = sum(p.amount for p in pagos_mes)
        total_esperado = sum(est.monthly_fee for est in student_list if est.active)

        # Get students with outstanding payments
        students_with_debt = [
            est
            for est in student_list
            if est.active and self.main_service.get_balance_by_id(est.id) < 0
        ]

        return {
            "periodo": f"{mes}/{year}",
            "total_esperado": total_esperado,
            "total_recaudado": total_recaudado,
            "porcentaje_cobertura": (total_recaudado / total_esperado * 100)
            if total_esperado > 0
            else 0,
            "students_with_debt": len(students_with_debt),
            "total_deuda": sum(-est.balance for est in students_with_debt),
            "detalle_pagos": pagos_mes,
        }
