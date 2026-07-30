import sqlite3
import sys
from pathlib import Path

import pytest

from migrations import run as migration_runner


def test_migration_runner_reads_current_history_schema(
    database_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration_directory = tmp_path / "migrations"
    migration_directory.mkdir()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run.py",
            "--db",
            str(database_path),
            "--dir",
            str(migration_directory),
        ],
    )

    assert migration_runner.main() == 0


def test_migration_runner_bootstraps_empty_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "fresh.sqlite3"
    migration_directory = Path(__file__).resolve().parents[1] / "migrations" / "sql"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run.py",
            "--db",
            str(database_path),
            "--dir",
            str(migration_directory),
        ],
    )

    assert migration_runner.main() == 0

    # Running a second time skips migrations already recorded.
    assert migration_runner.main() == 0
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """
            )
        }

        job_columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}

        applied_migrations = {
            row[0] for row in connection.execute("SELECT id FROM schema_migrations")
        }

        assert {
            "users",
            "technicians",
            "jobs",
            "locks",
            "time_off",
        } <= tables

        assert "custom_pest" in job_columns

        assert {
            "000_init.sql",
            "001_backfill_created_by_and_index.sql",
            "002_add_custom_pest_to_jobs.sql",
        } <= applied_migrations
