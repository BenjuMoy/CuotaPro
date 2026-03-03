"""
Steps to migrate:
    1) Write migration_X (Order desc, so first is the latest update).
    2) Add Callable to MIGRATIONS.
    3) Update db schema.
    4) Update db pragma version number in schema.
    5) Update models.
"""


def migration_1(conn): ...


MIGRATIONS = {
    1: migration_1,
}


def get_db_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def set_db_version(conn, version: int):
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn):
    current = get_db_version(conn)
    latest = max(MIGRATIONS.keys())

    while current < latest:
        next_version = current + 1

        if next_version not in MIGRATIONS:
            raise RuntimeError(...)

        try:
            conn.execute("BEGIN")
            MIGRATIONS[next_version](conn)
            set_db_version(conn, next_version)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        current = next_version


# def migrate(conn): # Old migration func
#    current = get_db_version(conn)
#    latest = max(MIGRATIONS.keys())
#
#    while current < latest:
#        next_version = current + 1
#
#        if next_version not in MIGRATIONS:
#            raise RuntimeError(f"No migration found for version {next_version}")
#
#        MIGRATIONS[next_version](conn)
#        set_db_version(conn, next_version)
#
#        current = next_version
