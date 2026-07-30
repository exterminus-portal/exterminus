import sqlite3
from pathlib import Path

from application import create_app


def test_empty_database_can_render_day_view(tmp_path: Path) -> None:
    database_path = tmp_path / "fresh.sqlite3"

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database_path),
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.test_client() as client:
        response = client.get("/day/2026-07-15")

    assert response.status_code == 200


def test_empty_database_records_applied_migrations(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "fresh.sqlite3"

    create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database_path),
            "WTF_CSRF_ENABLED": False,
        }
    )

    with sqlite3.connect(database_path) as connection:
        applied_migrations = {
            row[0] for row in connection.execute("SELECT id FROM schema_migrations")
        }

    assert {
        "000_init.sql",
        "001_backfill_created_by_and_index.sql",
        "002_add_custom_pest_to_jobs.sql",
    } <= applied_migrations
