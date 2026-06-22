from httpx import AsyncClient

from tests.test_boards import register_and_get_token


async def create_board(client: AsyncClient, token: str) -> dict:
    response = await client.post(
        "/api/boards",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Columns board"},
    )

    assert response.status_code == 200
    return response.json()


async def test_board_has_default_columns(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="default_columns_user",
        email="default_columns@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)

    response = await client.get(
        f"/api/boards/{board['public_id']}/columns",
        headers=headers,
    )

    assert response.status_code == 200

    columns = response.json()

    assert len(columns) == 3
    assert [column["position"] for column in columns] == [0, 1, 2]


async def test_create_column(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="create_column_user",
        email="create_column@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)

    response = await client.post(
        f"/api/boards/{board['public_id']}/columns",
        headers=headers,
        json={"title": "Review"},
    )

    assert response.status_code == 200

    column = response.json()

    assert column["title"] == "Review"
    assert column["position"] == 3
    assert "public_id" in column


async def test_update_column_title(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="update_column_user",
        email="update_column@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)

    columns_response = await client.get(
        f"/api/boards/{board['public_id']}/columns",
        headers=headers,
    )
    assert columns_response.status_code == 200

    column_id = columns_response.json()[0]["public_id"]

    response = await client.patch(
        f"/api/boards/{board['public_id']}/columns/{column_id}",
        headers=headers,
        json={"title": "Renamed column"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed column"


async def test_delete_column(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="delete_column_user",
        email="delete_column@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)

    create_response = await client.post(
        f"/api/boards/{board['public_id']}/columns",
        headers=headers,
        json={"title": "Temporary column"},
    )
    assert create_response.status_code == 200

    column_id = create_response.json()["public_id"]

    delete_response = await client.delete(
        f"/api/boards/{board['public_id']}/columns/{column_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Column deleted"

    columns_response = await client.get(
        f"/api/boards/{board['public_id']}/columns",
        headers=headers,
    )

    assert columns_response.status_code == 200

    column_ids = [column["public_id"] for column in columns_response.json()]
    assert column_id not in column_ids


async def test_other_user_cannot_create_column_on_private_board(client: AsyncClient):
    owner_token = await register_and_get_token(
        client,
        username="columns_owner",
        email="columns_owner@example.com",
    )
    owner_board = await create_board(client, owner_token)

    other_token = await register_and_get_token(
        client,
        username="columns_other",
        email="columns_other@example.com",
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await client.post(
        f"/api/boards/{owner_board['public_id']}/columns",
        headers=other_headers,
        json={"title": "Unauthorized column"},
    )

    assert response.status_code == 403
