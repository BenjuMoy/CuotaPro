from sqlite3 import Connection


class ReportRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    """
    ReportRepository (Read Model)

    Purpose:
    - Provide optimized read queries
    - Use SQL aggregation instead of domain logic
    - Return DTOs or primitives (NOT domain entities)

    Rules:
    - Must NOT use domain objects (Student, Account, Movement)
    - Must NOT enforce business rules
    - Must be read-only
    """

    def get_kpi_metrics(self, month: int, year: int) -> tuple[int, int, int, int]:
        query = """
        SELECT
            COUNT(s.id) as active_students,
            SUM(s.monthly_fee) as expected_income,

            COALESCE((
                SELECT SUM(m.amount)
                FROM movements m
                JOIN students s2 ON s2.id = m.student_id
                WHERE m.type = 'PAYMENT'
                AND m.month = ?
                AND m.year = ?
                AND s2.active = 1
            ), 0) as collected,

            COALESCE((
                SELECT SUM(CASE WHEN balance < 0 THEN -balance ELSE 0 END)
                FROM (
                    SELECT student_id, SUM(amount) as balance
                    FROM movements
                    GROUP BY student_id
                )
            ), 0) as total_debt

        FROM students s
        WHERE s.active = 1
        """

        row = self.conn.execute(query, (month, year)).fetchone()

        return (
            row["active_students"],
            row["expected_income"] or 0,
            row["collected"] or 0,
            row["total_debt"] or 0,
        )

    def get_students_without_fee(self, month: int, year: int) -> list[int]:
        query = """
        SELECT s.id
        FROM students s
        WHERE s.active = 1
        AND NOT EXISTS (
            SELECT 1 FROM movements m
            WHERE m.student_id = s.id
            AND m.type = 'FEE'
            AND m.month = ?
            AND m.year = ?
        )
        """

        rows = self.conn.execute(query, (month, year)).fetchall()
        return [row["id"] for row in rows]

    def are_fees_applied(self, month: int, year: int) -> bool:
        query = """
        SELECT COUNT(*) as missing
        FROM students s
        WHERE s.active = 1
        AND NOT EXISTS (
            SELECT 1 FROM movements m
            WHERE m.student_id = s.id
            AND m.type = 'FEE'
            AND m.month = ?
            AND m.year = ?
        )
        """

        row = self.conn.execute(query, (month, year)).fetchone()
        return row["missing"] == 0

    def get_debt_distribution(self) -> dict[str, int]:
        query = """
        WITH balances AS (
            SELECT
                s.id,
                s.monthly_fee,
                SUM(m.amount) as balance
            FROM students s
            LEFT JOIN movements m ON m.student_id = s.id
            WHERE s.active = 1
            GROUP BY s.id
        )
        SELECT
            SUM(CASE WHEN balance >= 0 THEN 1 ELSE 0 END) as al_dia,
            SUM(CASE WHEN balance < 0 AND ABS(balance) <= monthly_fee THEN 1 ELSE 0 END) as one,
            SUM(CASE WHEN balance < 0 AND ABS(balance) <= monthly_fee * 2 AND ABS(balance) > monthly_fee THEN 1 ELSE 0 END) as two,
            SUM(CASE WHEN balance < 0 AND ABS(balance) > monthly_fee * 2 THEN 1 ELSE 0 END) as three_plus
        FROM balances
        """

        row = self.conn.execute(query).fetchone()

        return {
            "Al día": row["al_dia"] or 0,
            "1 mes": row["one"] or 0,
            "2 meses": row["two"] or 0,
            "3+ meses": row["three_plus"] or 0,
        }

    def get_income_trend(self, limit: int = 6) -> list[tuple[int, int, int]]:
        query = """
        SELECT month, year, SUM(amount) as total
        FROM movements
        WHERE type = 'PAYMENT'
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        LIMIT ?
        """
        rows = self.conn.execute(query, (limit,)).fetchall()

        return [(r["month"], r["year"], r["total"]) for r in reversed(rows)]

    def get_teacher_distribution(self) -> dict[str, int]:
        query = """
        SELECT teacher, COUNT(*) as count
        FROM students
        WHERE active = 1
        GROUP BY teacher
        ORDER BY count ASC
        """

        rows = self.conn.execute(query).fetchall()
        return {row["teacher"]: row["count"] for row in rows}

    def get_salary(self, teacher: str) -> tuple[int, int]:
        query = """
        SELECT
            COUNT(*) as count,
            SUM(monthly_fee) as total
        FROM students
        WHERE teacher = ? AND active = 1
        """

        row = self.conn.execute(query, (teacher,)).fetchone()
        return row["count"], row["total"] or 0

    def search_student_overviews(
        self,
        name: str | None = None,
        teacher: str | None = None,
        active: bool | None = None,
        only_debtors: bool | None = None,
    ) -> list[dict]:
        conditions = []
        params = []

        if name:
            pattern = f"%{name}%"
            conditions.append("""
            (
                s.last_name LIKE ? COLLATE NOCASE OR
                s.first_name LIKE ? COLLATE NOCASE OR
                s.last_name || ' ' || s.first_name LIKE ? COLLATE NOCASE OR
                s.first_name || ' ' || s.last_name LIKE ? COLLATE NOCASE
            )
            """)
            params.extend([pattern] * 4)

        if teacher:
            conditions.append("s.teacher LIKE ? COLLATE NOCASE")
            params.append(f"%{teacher}%")

        if active is not None:
            conditions.append("s.active = ?")
            params.append(1 if active else 0)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 👇 balance computed in SQL
        query = f"""
        WITH balances AS (
            SELECT student_id, SUM(amount) as balance
            FROM movements
            GROUP BY student_id
        )
        SELECT
            s.*,
            COALESCE(b.balance, 0) as balance
        FROM students s
        LEFT JOIN balances b ON b.student_id = s.id
        {where_clause}
        """

        rows = self.conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            if only_debtors and row["balance"] >= 0:
                continue

            results.append(dict(row))

        return results
