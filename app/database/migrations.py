"""
Steps to migrate:
    1) Write migration_X (Order desc, so first is the latest update).
    2) Add Callable to MIGRATIONS.
    3) Update db schema.
    4) Update db pragma version number in schema.
    5) Update models.
"""

from sqlite3 import Connection


def migration_1(conn): ...


MIGRATIONS = {
    1: migration_1,
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
        migration = MIGRATIONS[current]

        migration(conn)

        current += 1
        set_db_version(conn, current)

        # next_version = current + 1

        # if next_version not in MIGRATIONS:
        #    raise RuntimeError(f"No migration found for version {next_version}")

        # MIGRATIONS[next_version](conn)
        # set_db_version(conn, next_version)

        # current = next_version
