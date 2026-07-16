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
