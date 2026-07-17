def test_manager_can_add_and_delete_time_off(
    client,
    db,
    manager_user,
    log_in,
):
    technician_id = db.execute(
        "INSERT INTO technicians (name) VALUES (?)",
        ("Test Technician",),
    ).lastrowid
    db.commit()
    log_in(manager_user)

    response = client.post(
        "/time_off/add",
        data={
            "technician_id": str(technician_id),
            "start_date": "2026-07-20",
            "end_date": "2026-07-22",
            "reason": "Vacation",
        },
    )

    assert response.status_code == 302

    entry = db.execute(
        """
        SELECT id, technician_id, start_date, end_date, reason
        FROM time_off
        WHERE technician_id = ?
        """,
        (technician_id,),
    ).fetchone()

    assert entry is not None
    assert entry["start_date"] == "2026-07-20"
    assert entry["end_date"] == "2026-07-22"
    assert entry["reason"] == "Vacation"

    response = client.post(f"/time_off/{entry['id']}/delete")

    assert response.status_code == 302
    assert (
        db.execute(
            "SELECT id FROM time_off WHERE id = ?",
            (entry["id"],),
        ).fetchone()
        is None
    )


def test_only_canonical_time_off_routes_are_registered(app):
    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/time_off/add" in rules
    assert "/time_off/<int:time_off_id>/delete" in rules
    assert "/timeoff/add" not in rules
    assert "/timeoff/delete/<int:timeoff_id>" not in rules
