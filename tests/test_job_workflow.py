def job_form_data(**overrides):
    """Return a minimally valid job-form submission."""
    data = {
        "title": "TestJob",
        "job_type": "termite",
        "start_date": "2026-07-15",
        "end_date": "2026-07-15",
        "start_time": "",
        "end_time": "",
        "time_range": "",
        "technician_id": "",
        "price": "",
        "notes": "",
        "rei_quantity": "",
        "rei_zip": "",
        "rei_city_name": "",
        "exclusion_subtype": "",
        "fumigation_type": "",
        "target_pest": "",
        "custom_pest": "",
        "custom_type": "",
    }
    data.update(overrides)
    return data


def test_daily_page_uses_one_add_job_control(
    client,
    manager_user,
    log_in,
):
    log_in(manager_user)

    response = client.get("/day/2026-07-15")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "+ Add Job" in html
    assert "+ Add Multi-Day" not in html


def test_daily_add_form_prefills_selected_date(
    client,
    manager_user,
    log_in,
):
    log_in(manager_user)

    response = client.get("/add_job/2026-07-15")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'name="start_date"' in html
    assert 'value="2026-07-15"' in html
    assert 'name="end_date"' in html
    assert 'value="2026-07-15"' in html


def test_add_single_day_job_derives_single_day_status(
    client,
    db,
    manager_user,
    log_in,
):
    log_in(manager_user)

    response = client.post(
        "/add_job/2026-07-15",
        data=job_form_data(),
    )

    assert response.status_code == 302

    count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    assert count == 1

    job = db.execute(
        """
            SELECT start_date, end_date, is_multiday
            FROM jobs
            """
    ).fetchone()

    assert job is not None
    assert job["start_date"] == "2026-07-15"
    assert job["end_date"] == "2026-07-15"
    assert job["is_multiday"] == 0


def test_edit_multiday_job_into_single_day_clears_multiday_status(
    client,
    db,
    manager_user,
    log_in,
):
    log_in(manager_user)

    cursor = db.execute(
        """
            INSERT INTO jobs (
                title,
                job_type,
                start_date,
                end_date,
                is_multiday,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
        (
            "Existing Multiday Job",
            "termite",
            "2026-07-15",
            "2026-07-17",
            1,
            manager_user["id"],
        ),
    )
    db.commit()

    response = client.post(
        f"/edit_job/{cursor.lastrowid}",
        data=job_form_data(
            title="Updated Single Day Job",
            start_date="2026-07-18",
            end_date="2026-07-18",
        ),
    )

    assert response.status_code == 302

    job = db.execute(
        """
            SELECT start_date, end_date, is_multiday
            FROM jobs
            WHERE id = ?
            """,
        (cursor.lastrowid,),
    ).fetchone()

    assert job["start_date"] == "2026-07-18"
    assert job["end_date"] == "2026-07-18"
    assert job["is_multiday"] == 0


def test_daily_add_form_can_create_multiday_job(
    client,
    db,
    manager_user,
    log_in,
):
    log_in(manager_user)

    response = client.post(
        "/add_job/2026-07-15",
        data=job_form_data(end_date="2026-07-17"),
    )

    assert response.status_code == 302

    job = db.execute(
        """
            SELECT start_date, end_date, is_multiday
            FROM jobs
            """
    ).fetchone()

    assert job is not None
    assert job["start_date"] == "2026-07-15"
    assert job["end_date"] == "2026-07-17"
    assert job["is_multiday"] == 1


def test_add_job_rejects_end_date_before_start_date(
    client,
    db,
    manager_user,
    log_in,
):
    log_in(manager_user)

    response = client.post(
        "/add_job/2026-07-15",
        data=job_form_data(end_date="2026-07-14"),
    )

    assert response.status_code == 302


def test_edit_job_form_contains_existing_dates(
    client,
    db,
    manager_user,
    log_in,
):
    log_in(manager_user)

    cursor = db.execute(
        """
            INSERT INTO jobs (
                title,
                job_type,
                start_date,
                end_date,
                is_multiday,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
        (
            "Existing Job",
            "termite",
            "2026-07-15",
            "2026-07-17",
            1,
            manager_user["id"],
        ),
    )
    db.commit()

    response = client.get(f"/edit_job/{cursor.lastrowid}")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'name="start_date"' in html
    assert 'value="2026-07-15"' in html
    assert 'name="end_date"' in html
    assert 'value="2026-07-17"' in html


def test_edit_job_updates_date_range_and_multiday_status(
    client,
    db,
    manager_user,
    log_in,
):
    log_in(manager_user)

    cursor = db.execute(
        """
            INSERT INTO jobs(
                title,
                job_type,
                start_date,
                end_date,
                is_multiday,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
        (
            "Existing Job",
            "termite",
            "2026-07-15",
            "2026-07-15",
            0,
            manager_user["id"],
        ),
    )
    db.commit()

    response = client.post(
        f"/edit_job/{cursor.lastrowid}",
        data=job_form_data(
            title="Updated Job",
            start_date="2026-07-16",
            end_date="2026-07-18",
        ),
    )

    assert response.status_code == 302

    job = db.execute(
        """
            SELECT title, start_date, end_date, is_multiday
            FROM jobs
            WHERE id = ?
            """,
        (cursor.lastrowid,),
    ).fetchone()

    assert job["title"] == "Updated Job"
    assert job["start_date"] == "2026-07-16"
    assert job["end_date"] == "2026-07-18"
    assert job["is_multiday"] == 1
