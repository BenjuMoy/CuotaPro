import random
from datetime import datetime
from pathlib import Path

from infrastructure.config.database_config import DatabaseConfig
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.schema import bootstrap_database, database_initialized

# Spanish first names and last names for realistic data
SPANISH_FIRST_NAMES = [
    "Juan",
    "María",
    "José",
    "Ana",
    "Luis",
    "Carmen",
    "Francisco",
    "Isabel",
    "Antonio",
    "Manuela",
    "José Luis",
    "María José",
    "Miguel",
    "Laura",
    "Pedro",
    "Cristina",
    "Javier",
    "Teresa",
    "Carlos",
    "Patricia",
    "David",
    "Marta",
    "Fernando",
    "Beatriz",
    "Jorge",
    "Sofía",
    "Sergio",
    "Elena",
    "Daniel",
    "Raquel",
    "Alberto",
    "Paula",
    "Rafael",
    "Nuria",
    "Roberto",
    "Silvia",
    "Ángel",
    "Miriam",
    "Víctor",
    "Yolanda",
    "Rubén",
    "Eva",
    "Juan Carlos",
    "Rocío",
    "Ricardo",
    "Inés",
    "Manuel",
    "Clara",
    "Óscar",
    "Angélica",
]

SPANISH_LAST_NAMES = [
    "García",
    "Rodríguez",
    "Martínez",
    "López",
    "González",
    "Pérez",
    "Sánchez",
    "Ramírez",
    "Torres",
    "Flores",
    "Rivera",
    "Gómez",
    "Díaz",
    "Cruz",
    "Morales",
    "Reyes",
    "Jiménez",
    "Moreno",
    "Muñoz",
    "Alvarez",
    "Fernández",
    "Gutiérrez",
    "Mendoza",
    "Vargas",
    "Castro",
    "Herrera",
    "Medina",
    "Ramos",
    "Ortiz",
]

# Phone number prefixes for Spanish mobile phones
PHONE_PREFIXES = ["6", "7"]

# Monthly fee options (in your local currency)
MONTHLY_FEES = [25000, 50000, 75000, 100000]


def generate_phone_number():
    """Generate a random Spanish phone number."""
    prefix = random.choice(PHONE_PREFIXES)
    # Generate 8 more digits
    rest = "".join(str(random.randint(0, 9)) for _ in range(8))
    return f"{prefix}{rest}"


def create_dummy_students_with_fees_and_payments(
    db_path: Path, student_count: int = 25
):
    """Create dummy students with fees and payments for current month/year."""
    db = DatabaseManager(db_path)

    # Initialize database if needed
    with db.connect() as conn:
        if not database_initialized(conn):
            print("Database not initialized. Creating schema...")
            bootstrap_database(conn)

    # Get current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    print(f"Creating data for {current_month}/{current_year}")

    # Generate and insert students
    student_ids = []
    with db.transaction() as conn:
        for i in range(student_count):
            first_name = random.choice(SPANISH_FIRST_NAMES)
            last_name = random.choice(SPANISH_LAST_NAMES)

            # Generate up to 3 phone numbers
            phone1 = generate_phone_number()
            phone2 = generate_phone_number() if random.random() > 0.7 else ""
            phone3 = generate_phone_number() if random.random() > 0.9 else ""

            # Generate teacher, book, course, and year values
            teacher = f"Profesor {random.randint(1, 3)}"
            book = f"Libro {random.randint(1, 3)}"
            school = f"Escuela {random.randint(1, 3)}"
            course = f"Curso {random.randint(1, 3)}"
            year = f"Año escolar {random.randint(1, 3)}"

            # Random monthly fee
            monthly_fee = random.choice(MONTHLY_FEES)

            # All students will be active (active=1)
            active = 1

            # Insert student
            cursor = conn.execute(
                """
                INSERT INTO students (
                    active, last_name, first_name, phone1, phone2, phone3,                    teacher, book, course, school, year, monthly_fee
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    active,
                    last_name,
                    first_name,
                    phone1,
                    phone2,
                    phone3,
                    teacher,
                    book,
                    course,
                    school,
                    year,
                    monthly_fee,
                ),
            )

            student_id = cursor.lastrowid
            student_ids.append((student_id, monthly_fee))

            print(
                f"Created student: {first_name} {last_name} - {teacher} - {monthly_fee}"
            )

    # Create fees and payments
    with db.transaction() as conn:
        for student_id, monthly_fee in student_ids:
            # Create a fee for the current month
            cursor = conn.execute(
                """
                INSERT INTO movements (
                    student_id, reference_id, type, amount, month, year
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (student_id, None, "FEE", -monthly_fee, current_month, current_year),
            )

            fee_id = cursor.lastrowid

            # Randomly determine if the student has paid (70% chance)
            has_paid = random.random() > 0.3

            if has_paid:
                # Create a payment for the fee (could be full or partial)
                if random.random() > 0.2:  # 80% chance of full payment
                    payment_amount = monthly_fee
                else:  # 20% chance of partial payment
                    payment_amount = int(monthly_fee * random.uniform(0.5, 0.9))

                cursor = conn.execute(
                    """
                    INSERT INTO movements (
                        student_id, reference_id, type, amount, month, year
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        student_id,
                        None,
                        "PAYMENT",
                        payment_amount,
                        current_month,
                        current_year,
                    ),
                )

                payment_id = cursor.lastrowid
                print(
                    f"Created fee: -{monthly_fee} and payment: +{payment_amount} for student {student_id}"
                )
            else:
                print(f"Created fee: -{monthly_fee} (unpaid) for student {student_id}")

    print(
        f"Successfully created {student_count} dummy students with fees and payments for {current_month}/{current_year}."
    )


if __name__ == "__main__":
    # Path to your database file
    db_config = DatabaseConfig()
    db_config.ensure_dirs()

    # Create 25 dummy students with fees and payments
    create_dummy_students_with_fees_and_payments(db_config.database_path, 25)
