"""
Steps to migrate:
    1) Write migration_X (Order desc, so first is the latest update).
    2) Add Callable to MIGRATIONS.
    3) Update db schema.
    4) Update db pragma version number in schema.
    5) Update models.
"""

from sqlite3 import Connection


def migration_3(conn: Connection):
    conn.execute("""
    DROP INDEX IF EXISTS idx_unique_student;
    """)


def migration_2(conn: Connection):
    conn.executescript("""
        DROP INDEX IF EXISTS idx_active_students;
        CREATE INDEX idx_active_students
        ON students(active);

        DROP INDEX  IF EXISTS idx_teacher_students;
        CREATE INDEX idx_teacher_students
        ON students(teacher);

        DROP INDEX IF EXISTS idx_unique_student;
        CREATE INDEX idx_unique_student
        ON students(last_name, first_name, teacher);
    """)


MIGRATIONS = {
    2: migration_2,
    3: migration_3,
}


def get_db_version(conn: Connection):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def set_db_version(conn: Connection, version: int):
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn: Connection):
    current = get_db_version(conn)
    latest = max(MIGRATIONS.keys())

    if current > latest:
        raise RuntimeError("Database version is newer than application")

    while current < latest:
        next_version = current + 1
        migration = MIGRATIONS[next_version]

        migration(conn)

        set_db_version(conn, next_version)
        current = next_version
