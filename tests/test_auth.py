from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_register_user(client):
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "test_user",
            "email": "test_user@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"

    assert "refresh_token" in response.cookies


async def test_register_duplicate_email_returns_error(client):
    payload = {
        "username": "first_user",
        "email": "duplicate@example.com",
        "password": "password123",
    }

    first_response = await client.post("/api/auth/register", json=payload)
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/auth/register",
        json={
            **payload,
            "username": "second_user",
        },
    )

    assert second_response.status_code == 400

    data = second_response.json()
    assert data["error"] == "Email already registered"


async def test_login_user(client):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "login_user",
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/auth/login",
        json={
            "login": "login@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert "refresh_token" in login_response.cookies


async def test_login_with_wrong_password_returns_error(client):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "wrong_password_user",
            "email": "wrong_password@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    response = await client.post(
        "/api/auth/login",
        json={
            "login": "wrong_password@example.com",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401


async def test_refresh_access_token(client):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "refresh_user",
            "email": "refresh@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201
    assert "refresh_token" in register_response.cookies

    refresh_response = await client.post("/api/auth/refresh")

    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"


async def test_refresh_without_cookie_returns_401(client):
    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401


async def test_logout_revokes_current_session(client):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "logout_user",
            "email": "logout@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201
    assert "refresh_token" in client.cookies

    logout_response = await client.post("/api/auth/logout")

    assert logout_response.status_code == 204

    refresh_response = await client.post("/api/auth/refresh")

    assert refresh_response.status_code == 401


async def test_get_active_sessions(client: AsyncClient):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "sessions_user",
            "email": "sessions@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as second_client:
        login_response = await second_client.post(
            "/api/auth/login",
            json={
                "login": "sessions@example.com",
                "password": "password123",
            },
        )

        assert login_response.status_code == 200

    sessions_response = await client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert sessions_response.status_code == 200

    sessions = sessions_response.json()

    assert len(sessions) == 2

    for session in sessions:
        assert "session_id" in session
        assert "created_at" in session
        assert "last_used_at" in session


async def test_logout_all_revokes_all_sessions(client: AsyncClient):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "logout_all_user",
            "email": "logout_all@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    first_access_token = register_response.json()["access_token"]

    login_response = await client.post(
        "/api/auth/login",
        json={
            "login": "logout_all@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    second_access_token = login_response.json()["access_token"]

    logout_all_response = await client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {second_access_token}"},
    )

    assert logout_all_response.status_code == 204

    sessions_response = await client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {first_access_token}"},
    )

    assert sessions_response.status_code == 401


async def test_logout_specific_device(client: AsyncClient):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "device_logout_user",
            "email": "device_logout@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    login_response = await client.post(
        "/api/auth/login",
        json={
            "login": "device_logout@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    sessions_response = await client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert sessions_response.status_code == 200

    sessions = sessions_response.json()
    assert len(sessions) == 2

    session_id_to_delete = sessions[0]["session_id"]

    delete_response = await client.delete(
        f"/api/auth/sessions/{session_id_to_delete}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert delete_response.status_code == 204

    updated_sessions_response = await client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert updated_sessions_response.status_code == 200

    updated_sessions = updated_sessions_response.json()

    assert len(updated_sessions) == 1
    assert updated_sessions[0]["session_id"] != session_id_to_delete


async def test_user_cannot_delete_another_users_session(client: AsyncClient):
    first_register = await client.post(
        "/api/auth/register",
        json={
            "username": "session_owner",
            "email": "session_owner@example.com",
            "password": "password123",
        },
    )
    assert first_register.status_code == 201

    owner_token = first_register.json()["access_token"]

    owner_sessions_response = await client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_sessions_response.status_code == 200

    owner_session_id = owner_sessions_response.json()[0]["session_id"]

    other_register = await client.post(
        "/api/auth/register",
        json={
            "username": "session_attacker",
            "email": "session_attacker@example.com",
            "password": "password123",
        },
    )
    assert other_register.status_code == 201

    attacker_token = other_register.json()["access_token"]

    response = await client.delete(
        f"/api/auth/sessions/{owner_session_id}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )

    assert response.status_code == 404
