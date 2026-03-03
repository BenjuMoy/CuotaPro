from app.models.models import Student


class StudentSearchEngine:
    def __init__(self, student_list: list[Student]):
        self.students = student_list

    def search(self, **criteria):
        """
        Flexible search method that accepts multiple criteria.
        Example: search(last_name="García", active=True, teacher="Pérez")
        """
        results = []

        for student in self.students:
            matches_all = True

            for field, value in criteria.items():
                if not hasattr(student, field):
                    continue

                field_value = getattr(student, field)

                if isinstance(field_value, str) and isinstance(value, str):
                    if value.lower() not in field_value.lower():
                        matches_all = False
                        break
                elif field_value != value:
                    matches_all = False
                    break

            if matches_all:
                results.append(student)

        return results

    def search_by_name_parts(self, name_parts: list[str]) -> list[Student]:
        """Search by any part of the name (first name, last name, or both)"""
        results = []
        normalized_parts = [part.lower().strip() for part in name_parts]

        for student in self.students:
            full_name = f"{student.last_name} {student.first_name}".lower()

            if all(part in full_name for part in normalized_parts):
                results.append(student)

        return results


if __name__ == "__main__":
    print(list)
