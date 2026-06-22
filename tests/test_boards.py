from httpx import AsyncClient


async def register_and_get_token(
    client: AsyncClient,
    username: str = "board_user",
    email: str = "board_user@example.com",
) -> str:
    response = await client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    return response.json()["access_token"]


async def test_create_board(client: AsyncClient):
    token = await register_and_get_token(client)

    response = await client.post(
        "/api/boards",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My first board",
            "description": "Board for tests",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "My first board"
    assert data["description"] == "Board for tests"
    assert "public_id" in data


async def test_get_boards(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="boards_list_user",
        email="boards_list@example.com",
    )

    create_response = await client.post(
        "/api/boards",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "First board",
        },
    )

    assert create_response.status_code == 200

    response = await client.get(
        "/api/boards",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    boards = response.json()

    assert len(boards) == 1
    assert boards[0]["title"] == "First board"
    assert boards[0]["role"] == "owner"
    assert boards[0]["columns_count"] == 3
    assert boards[0]["cards_count"] == 0


async def test_create_board_without_token_returns_401(client: AsyncClient):
    response = await client.post(
        "/api/boards",
        json={
            "title": "Forbidden board",
        },
    )

    assert response.status_code == 401


async def test_get_board_by_id(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="get_board_user",
        email="get_board@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/boards",
        headers=headers,
        json={
            "title": "Detailed board",
            "description": "Board description",
        },
    )
    assert create_response.status_code == 200

    board_id = create_response.json()["public_id"]

    response = await client.get(
        f"/api/boards/{board_id}",
        headers=headers,
    )

    assert response.status_code == 200

    board = response.json()

    assert board["public_id"] == board_id
    assert board["title"] == "Detailed board"
    assert board["description"] == "Board description"
    assert board["board_role"] == "owner"
    assert len(board["columns"]) == 3


async def test_other_user_cannot_get_private_board(client: AsyncClient):
    owner_token = await register_and_get_token(
        client,
        username="owner_user",
        email="owner@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create_response = await client.post(
        "/api/boards",
        headers=owner_headers,
        json={"title": "Private board"},
    )
    assert create_response.status_code == 200

    board_id = create_response.json()["public_id"]

    other_token = await register_and_get_token(
        client,
        username="other_user",
        email="other@example.com",
    )

    response = await client.get(
        f"/api/boards/{board_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


async def test_owner_can_update_board(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="update_board_user",
        email="update_board@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/boards",
        headers=headers,
        json={
            "title": "Old title",
            "description": "Old description",
        },
    )
    assert create_response.status_code == 200

    board_id = create_response.json()["public_id"]

    response = await client.patch(
        f"/api/boards/{board_id}",
        headers=headers,
        json={
            "title": "New title",
            "description": "New description",
        },
    )

    assert response.status_code == 200

    board = response.json()
    assert board["public_id"] == board_id
    assert board["title"] == "New title"
    assert board["description"] == "New description"


async def test_updated_board_is_returned_with_new_data(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="persist_board_user",
        email="persist_board@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/boards",
        headers=headers,
        json={"title": "Before update"},
    )
    assert create_response.status_code == 200

    board_id = create_response.json()["public_id"]

    update_response = await client.patch(
        f"/api/boards/{board_id}",
        headers=headers,
        json={"title": "After update"},
    )
    assert update_response.status_code == 200

    get_response = await client.get(
        f"/api/boards/{board_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "After update"


async def test_owner_can_delete_board(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="delete_board_user",
        email="delete_board@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/boards",
        headers=headers,
        json={"title": "Board to delete"},
    )
    assert create_response.status_code == 200

    board_id = create_response.json()["public_id"]

    delete_response = await client.delete(
        f"/api/boards/{board_id}",
        headers=headers,
    )

    # Сначала посмотри, что возвращает твой endpoint: обычно 200 или 204.
    assert delete_response.status_code == 200

    get_response = await client.get(
        f"/api/boards/{board_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


async def test_other_user_cannot_delete_board(client: AsyncClient):
    owner_token = await register_and_get_token(
        client,
        username="delete_owner",
        email="delete_owner@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create_response = await client.post(
        "/api/boards",
        headers=owner_headers,
        json={"title": "Owner board"},
    )
    assert create_response.status_code == 200

    board_id = create_response.json()["public_id"]

    other_token = await register_and_get_token(
        client,
        username="delete_other",
        email="delete_other@example.com",
    )

    response = await client.delete(
        f"/api/boards/{board_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403
