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
