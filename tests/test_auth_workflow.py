from werkzeug.security import check_password_hash


def test_forced_password_reset_updates_password_and_clears_gate(
    client,
    db,
    manager_user,
    log_in,
):
    db.execute(
        "UPDATE users SET must_reset_password = 1 WHERE id = ?",
        (manager_user["id"],),
    )
    db.commit()
    log_in(manager_user)

    with client.session_transaction() as session:
        session["must_change_pw"] = True

    response = client.post(
        "/force-password-reset",
        data={
            "new_password": "new-secure-password",
            "confirm_password": "new-secure-password",
        },
    )

    assert response.status_code == 302

    user = db.execute(
        """
            SELECT password, must_reset_password
            FROM users
            WHERE id = ?
            """,
        (manager_user["id"],),
    ).fetchone()

    assert check_password_hash(user["password"], "new-secure-password")
    assert user["must_reset_password"] == 0

    with client.session_transaction() as session:
        assert session["must_change_pw"] is False


def test_only_supported_password_reset_routes_are_registered(app):
    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/change_password" in rules
    assert "/force-password-reset" in rules
    assert "/forgot" not in rules
