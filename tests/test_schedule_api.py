def test_day_schedule_is_available_anonymously(client):
    response = client.get("/api/v1/schedule/day/2026-07-15")

    assert response.status_code == 200
    assert response.get_json() == {
        "date": "2026-07-15",
        "locked": False,
        "jobs": [],
        "time_off": [],
    }


def test_day_schedule_rejects_non_iso_date(client):
    response = client.get("/api/v1/schedule/day/not-a-date")

    assert response.status_code == 400
    assert response.get_json() == {"error": "selected_date must use YYYY-MM-DD format"}


def test_day_schedule_reports_lock_state(
    client,
    db,
    manager_user,
):
    db.execute(
        """
            INSERT INTO locks (date, locked_by)
            VALUES (?,?)
            """,
        ("2026-07-15", manager_user["id"]),
    )
    db.commit()

    response = client.get("/api/v1/schedule/day/2026-07-15")

    assert response.status_code == 200
    assert response.get_json()["locked"] is True


def test_day_schedule_includes_overlapping_multiday_job(
    client,
    db,
    manager_user,
):
    technician_id = db.execute(
        """
            INSERT INTO technicians (name)
            VALUES (?)
            """,
        ("Test Technician",),
    ).lastrowid

    db.execute(
        """
            INSERT INTO jobs (
            title,
            start_date,
            end_date,
            job_type,
            technician_id,
            is_multiday,
            created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
        (
            "Three-day treatment",
            "2026-07-14",
            "2026-07-16",
            "termite",
            technician_id,
            1,
            manager_user["id"],
        ),
    )
    db.commit()

    response = client.get("/api/v1/schedule/day/2026-07-15")

    assert response.status_code == 200

    jobs = response.get_json()["jobs"]

    assert len(jobs) == 1
    assert jobs[0]["display_title"] == "Three-day treatment"
    assert jobs[0]["technician_name"] == "Test Technician"
    assert jobs[0]["is_mid"] == 1


def test_day_schedule_includes_overlapping_time_off(
    client,
    db,
):
    technician_id = db.execute(
        """
            INSERT INTO technicians (name)
            VALUES (?)
            """,
        ("Vacationing Technician",),
    ).lastrowid

    db.execute(
        """
            INSERT INTO time_off (
                technician_id,
                start_date,
                end_date,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
        (
            technician_id,
            "2026-07-14",
            "2026-07-16",
            "Vacation",
        ),
    )
    db.commit()

    response = client.get("/api/v1/schedule/day/2026-07-15")

    assert response.status_code == 200

    time_off = response.get_json()["time_off"]

    assert len(time_off) == 1
    assert time_off[0]["tech_name"] == "Vacationing Technician"
    assert time_off[0]["reason"] == "Vacation"


def test_health_endpoint_reports_exterminus(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "service": "exterminus",
        "status": "ok",
    }
