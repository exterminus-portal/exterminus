"""Database utilities for ExTerminus (SQLite).

Provides:
    - ``get_database()``: open a configured SQLite connection (WAL, FKs on).
    - ``ensure_pragmas()``: no-op that touches a connection to apply PRAGMAs.
    - ``init_db()``: create tables if missing and bootstrap a default admin.

Notes:
    - The database path comes from the Flask ``DATABASE`` configuration.
    - PRAGMAs: ``foreign_keys=ON`` and ``journal_mode=WAL``.
"""

import sqlite3
from pathlib import Path

from flask import current_app
from werkzeug.security import generate_password_hash
from migrations.run import apply_migrations

from utils.logger import setup_logger

logger = setup_logger(level=0)
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations" / "sql"


def get_database() -> sqlite3.Connection:
    database = current_app.config["DATABASE"]

    if database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)

    logger.debug("Connecting to sqlite3: %s", database)

    conn = sqlite3.connect(database, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_pragmas() -> None:
    """Ensure database PRAGMAs are applied.

    Opens and closes a connection so the PRAGMA settings in ``get_database()`` take effect at least once during app lifetime.

    Returns:
        None
    """
    conn = get_database()
    conn.close()


def init_db() -> None:
    """apply pending migrations and bootstrap a default admin."""

    logger.debug("Initializing database...")
    conn = get_database()

    try:
        apply_migrations(
            conn,
            MIGRATIONS_DIR,
        )

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM users")

        if cur.fetchone()["c"] == 0:
            logger.warning(
                "No users found; creating default admin."
                "(username 'admin' / password 'changeme')"
            )
            cur.execute(
                """
                 INSERT INTO users (
                    first_name,
                    last_name,
                    username,
                    password,
                    role,
                    must_reset_password
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "Admin",
                    "User",
                    "admin",
                    generate_password_hash("changeme"),
                    "admin",
                    1,
                ),
            )

        conn.commit()
    finally:
        conn.close()

        logger.info("Database ready.")
