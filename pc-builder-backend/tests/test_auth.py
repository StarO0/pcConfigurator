def test_token_rotation_and_sessions(client):
    email = "rotation@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Rotation", "password": "Strong-password-123"},
    )
    assert registered.status_code == 201, registered.text
    first = registered.json()
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == email

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert refreshed.status_code == 200
    second = refreshed.json()
    assert second["refresh_token"] != first["refresh_token"]
    sessions = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert sessions.status_code == 200
    assert sessions.json()

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reused.status_code == 401
    compromised = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert compromised.status_code == 401


def test_password_reset(client):
    email = "reset@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Reset User", "password": "Old-password-123"},
    )
    forgot = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    token = forgot.json()["token"]
    assert token
    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "New-password-456"},
    )
    assert reset.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "New-password-456"},
    )
    assert login.status_code == 200
