import sqlite3
from pathlib import Path
import pytest
from application import create_app


@pytest.fixture()
def database_path(tmp_path: Path) -> Path:
    """Create a fresh database using the current production-schema snapshot."""
    path = tmp_path / "exterminus.sqlite3"
    schema_path = Path(__file__).parent / "fixtures" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(path) as connection:
        connection.executescript(schema)

    return path


@pytest.fixture()
def app(database_path: Path):
    """Create an isolated ExTerminus application for one test."""
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database_path),
            "WTF_CSRF_ENABLED": False,
        }
    )

    yield test_app


@pytest.fixture()
def client(app):
    """Provide Flask's HTTP test client."""
    return app.test_client()


@pytest.fixture()
def db(database_path: Path):
    """Provide direct database access for arranging and inspecting test data."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    yield connection

    connection.close()


@pytest.fixture()
def user_factory(db):
    """Create users for route and permission tests."""

    def _create_user(
        *,
        username: str,
        role: str,
        first_name: str = "Test",
        last_name: str = "User",
    ):
        cursor = db.execute(
            """
        INSERT INTO users (
            first_name,
            last_name,
            username,
            password,
            role,
            must_reset_password
        )
        VALUES (?, ?, ?, ?, ?, 0)
        """,
            (
                first_name,
                last_name,
                username,
                "unused-in-tests",
                role,
            ),
        )
        db.commit()

        return db.execute(
            "SELECT * FROM users WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return _create_user


@pytest.fixture()
def manager_user(user_factory):
    """Create a manager for job-workflow tests."""
    return user_factory(
        username="test-manager",
        role="manager",
        first_name="Test",
        last_name="Manager",
    )


@pytest.fixture()
def log_in(client):
    """Authenticate a database user directly through the test session."""

    def _log_in(user):
        with client.session_transaction() as session:
            session["user"] = {
                "user_id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "username": user["username"],
                "role": user["role"],
            }
            session["must_change_pw"] = False

    return _log_in
