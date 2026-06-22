from httpx import AsyncClient

from tests.test_boards import register_and_get_token
from tests.test_columns import create_board


async def register_admin(
    client: AsyncClient,
    admin_user,
    verified_user,
    *,
    username: str,
    email: str,
) -> str:
    token = await register_and_get_token(
        client,
        username=username,
        email=email,
    )
    await admin_user(email)
    await verified_user(email)
    return token


async def create_owner_and_board(client: AsyncClient):
    owner_token = await register_and_get_token(
        client,
        username="admin_test_owner",
        email="admin_test_owner@example.com",
    )

    board = await create_board(client, owner_token)

    return owner_token, board


async def test_admin_can_get_any_private_board(
    client: AsyncClient,
    admin_user,
):
    owner_token = await register_and_get_token(
        client,
        username="admin_board_owner",
        email="admin_board_owner@example.com",
    )

    board = await create_board(client, owner_token)

    admin_token = await register_and_get_token(
        client,
        username="super_admin",
        email="super_admin@example.com",
    )
    await admin_user("super_admin@example.com")

    response = await client.get(
        f"/api/boards/{board['public_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["public_id"] == board["public_id"]


async def test_admin_can_update_any_board(
    client: AsyncClient,
    admin_user,
):
    owner_token = await register_and_get_token(
        client,
        username="admin_update_owner",
        email="admin_update_owner@example.com",
    )

    board = await create_board(client, owner_token)

    admin_token = await register_and_get_token(
        client,
        username="admin_update_user",
        email="admin_update_user@example.com",
    )
    await admin_user("admin_update_user@example.com")

    response = await client.patch(
        f"/api/boards/{board['public_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Updated by admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated by admin"


async def test_admin_can_add_member_to_any_board(
    client: AsyncClient,
    admin_user,
    verified_user,
):
    owner_token = await register_and_get_token(
        client,
        username="admin_members_owner",
        email="admin_members_owner@example.com",
    )

    board = await create_board(client, owner_token)

    admin_token = await register_and_get_token(
        client,
        username="admin_members_user",
        email="admin_members_user@example.com",
    )
    await admin_user("admin_members_user@example.com")
    await verified_user("admin_members_user@example.com")

    await register_and_get_token(
        client,
        username="admin_members_target",
        email="admin_members_target@example.com",
    )

    response = await client.post(
        f"/api/members/{board['public_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "admin_members_target",
            "role": "viewer",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "admin_members_target"


async def test_admin_can_manage_columns_and_cards(
    client: AsyncClient,
    admin_user,
    verified_user,
):
    _, board = await create_owner_and_board(client)
    board_id = board["public_id"]

    admin_token = await register_admin(
        client,
        admin_user,
        verified_user,
        username="admin_cards_user",
        email="admin_cards_user@example.com",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    columns_response = await client.get(
        f"/api/boards/{board_id}/columns",
        headers=headers,
    )
    assert columns_response.status_code == 200

    first_column_id = columns_response.json()[0]["public_id"]

    create_column_response = await client.post(
        f"/api/boards/{board_id}/columns",
        headers=headers,
        json={"title": "Admin column"},
    )
    assert create_column_response.status_code == 200

    admin_column_id = create_column_response.json()["public_id"]

    update_column_response = await client.patch(
        f"/api/boards/{board_id}/columns/{admin_column_id}",
        headers=headers,
        json={"title": "Renamed by admin"},
    )
    assert update_column_response.status_code == 200
    assert update_column_response.json()["title"] == "Renamed by admin"

    create_card_response = await client.post(
        f"/api/columns/{first_column_id}/cards",
        headers=headers,
        json={
            "title": "Admin card",
            "description": "Created by admin",
        },
    )
    assert create_card_response.status_code == 200

    card_id = create_card_response.json()["public_id"]

    update_card_response = await client.patch(
        f"/api/cards/{card_id}",
        headers=headers,
        json={
            "title": "Updated admin card",
        },
    )
    assert update_card_response.status_code == 200
    assert update_card_response.json()["title"] == "Updated admin card"

    delete_card_response = await client.delete(
        f"/api/cards/{card_id}",
        headers=headers,
    )
    assert delete_card_response.status_code == 204

    delete_column_response = await client.delete(
        f"/api/boards/{board_id}/columns/{admin_column_id}",
        headers=headers,
    )
    assert delete_column_response.status_code == 200


async def test_admin_can_update_any_board_layout(
    client: AsyncClient,
    admin_user,
    verified_user,
):
    _, board = await create_owner_and_board(client)
    board_id = board["public_id"]

    admin_token = await register_admin(
        client,
        admin_user,
        verified_user,
        username="admin_layout_user",
        email="admin_layout_user@example.com",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    columns_response = await client.get(
        f"/api/boards/{board_id}/columns",
        headers=headers,
    )
    assert columns_response.status_code == 200

    columns = columns_response.json()
    first_column_id = columns[0]["public_id"]
    second_column_id = columns[1]["public_id"]

    create_card_response = await client.post(
        f"/api/columns/{first_column_id}/cards",
        headers=headers,
        json={"title": "Card moved by admin"},
    )
    assert create_card_response.status_code == 200

    card_id = create_card_response.json()["public_id"]

    response = await client.patch(
        f"/api/boards/{board_id}/layout",
        headers=headers,
        json={
            "cards": [
                {
                    "card_id": card_id,
                    "column_id": second_column_id,
                    "position": 0,
                }
            ]
        },
    )

    assert response.status_code == 200

    cards_response = await client.get(
        f"/api/columns/{second_column_id}/cards",
        headers=headers,
    )

    assert cards_response.status_code == 200
    assert cards_response.json()[0]["public_id"] == card_id


async def test_admin_can_manage_members_on_any_board(
    client: AsyncClient,
    admin_user,
    verified_user,
):
    _, board = await create_owner_and_board(client)
    board_id = board["public_id"]

    admin_token = await register_admin(
        client,
        admin_user,
        verified_user,
        username="admin_members_user",
        email="admin_members_user@example.com",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    await register_and_get_token(
        client,
        username="admin_member_target",
        email="admin_member_target@example.com",
    )

    add_response = await client.post(
        f"/api/members/{board_id}",
        headers=headers,
        json={
            "username": "admin_member_target",
            "role": "viewer",
        },
    )

    assert add_response.status_code == 200
    assert add_response.json()["role"] == "viewer"

    update_response = await client.patch(
        f"/api/members/{board_id}/admin_member_target",
        headers=headers,
        json={"role": "editor"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["role"] == "editor"

    delete_response = await client.delete(
        f"/api/members/{board_id}/admin_member_target",
        headers=headers,
    )

    assert delete_response.status_code == 204

    async def test_admin_can_see_any_private_board_in_list(
        client: AsyncClient,
        admin_user,
        verified_user,
    ):
        _, board = await create_owner_and_board(client)

        admin_token = await register_admin(
            client,
            admin_user,
            verified_user,
            username="admin_list_user",
            email="admin_list_user@example.com",
        )

        response = await client.get(
            "/api/boards",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        boards = response.json()
        assert any(item["public_id"] == board["public_id"] for item in boards)


async def test_admin_can_delete_any_board(
    client: AsyncClient,
    admin_user,
    verified_user,
):
    _, board = await create_owner_and_board(client)

    admin_token = await register_admin(
        client,
        admin_user,
        verified_user,
        username="admin_delete_board_user",
        email="admin_delete_board_user@example.com",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    delete_response = await client.delete(
        f"/api/boards/{board['public_id']}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    get_response = await client.get(
        f"/api/boards/{board['public_id']}",
        headers=headers,
    )

    assert get_response.status_code == 404
