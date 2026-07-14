def test_month_view_loads_anonymously(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'class="calendar-table"' in response.data


def test_day_view_loads_anonymously(client):
    response = client.get("/day/2026-07-15")

    assert response.status_code == 200
    assert b"Jobs for Wednesday, July 15, 2026" in response.data
