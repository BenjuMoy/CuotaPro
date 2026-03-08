from sqlite3 import Connection


def database_initialized(conn):
    row = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='students'
    """).fetchone()
    return row is not None


def bootstrap_database(conn: Connection):
    # --------------------------------------------------------------------------- #
    # Create tables
    # --------------------------------------------------------------------------- #

    conn.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
            last_name TEXT NOT NULL CHECK(length(last_name) BETWEEN 1 AND 50),
            first_name TEXT NOT NULL CHECK(length(first_name) BETWEEN 1 AND 50),
            phone1 TEXT NOT NULL CHECK(length(phone1) BETWEEN 1 AND 20),
            phone2 TEXT DEFAULT '' CHECK(length(phone2) <= 20),
            phone3 TEXT DEFAULT '' CHECK(length(phone3) <= 20),
            teacher TEXT NOT NULL CHECK(length(teacher) BETWEEN 1 AND 20),
            book TEXT DEFAULT '' CHECK(length(book) <= 20),
            course TEXT DEFAULT '' CHECK(length(course) <= 20),
            school TEXT DEFAULT '' CHECK(length(school) <= 20),
            year TEXT DEFAULT '' CHECK(length(year) <= 20),
            monthly_fee INTEGER NOT NULL CHECK (monthly_fee BETWEEN 1 AND 500000)
        );
    """)

    conn.execute("""
        CREATE TABLE movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            reference_id INTEGER DEFAULT NULL,
            type TEXT NOT NULL CHECK(type IN ('FEE', 'PAYMENT', 'REVERSED')),
            amount INTEGER NOT NULL CHECK (
                (type = 'FEE' AND amount BETWEEN -500000 AND -1 AND reference_id IS NULL)
                OR (type = 'PAYMENT' AND amount BETWEEN 1 AND 500000 AND reference_id IS NULL)
                OR (type = 'REVERSED' AND ABS(amount) <= 500000 AND reference_id IS NOT NULL)
            ),
            month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
            year INTEGER NOT NULL CHECK(year >= 2000),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(reference_id) REFERENCES movements(id) ON DELETE RESTRICT,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE RESTRICT
        );
    """)

    # --------------------------------------------------------------------------- #
    # Indexes
    # --------------------------------------------------------------------------- #

    # Enforce 1 fee per month
    conn.execute("""
        CREATE UNIQUE INDEX idx_unique_fee
        ON movements(student_id, month, year)
        WHERE type = 'FEE';
        """)

    # Enforce Unique students
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_student
        ON students (last_name, first_name, phone1);
        """)

    # Enforce Unique reverses
    conn.execute("""
        CREATE UNIQUE INDEX idx_unique_reversal
        ON movements (reference_id)
        WHERE reference_id IS NOT NULL;
        """)

    conn.execute("""
        CREATE INDEX idx_active_students
        ON students(active);
        """)

    conn.execute("""
        CREATE INDEX idx_teacher_students
        ON students(teacher);
        """)

    conn.execute("""
        CREATE INDEX idx_movements_student_period
        ON movements(student_id, year, month);
        """)

    conn.execute("""
        CREATE INDEX idx_movements_student
        ON movements(student_id);
        """)

    # Set database version
    conn.execute("PRAGMA user_version = 3")

    #        row = self.connection.execute(
    #            "SELECT COUNT(*) as count FROM schema_version"
    #        ).fetchone()
