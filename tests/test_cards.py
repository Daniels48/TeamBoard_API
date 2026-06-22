from httpx import AsyncClient

from tests.test_boards import register_and_get_token
from tests.test_columns import create_board


async def get_first_column_id(client: AsyncClient, board_id: str, headers: dict[str, str]) -> str:
    response = await client.get(
        f"/api/boards/{board_id}/columns",
        headers=headers,
    )

    assert response.status_code == 200

    columns = response.json()
    assert len(columns) == 3

    return columns[0]["public_id"]


async def test_create_card(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="create_card_user",
        email="create_card@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)
    column_id = await get_first_column_id(client, board["public_id"], headers)

    response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=headers,
        json={
            "title": "First task",
            "description": "Card description",
        },
    )

    assert response.status_code == 200

    card = response.json()

    assert card["title"] == "First task"
    assert card["description"] == "Card description"
    assert card["position"] == 0
    assert "public_id" in card


async def test_get_cards_in_column(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="list_cards_user",
        email="list_cards@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)
    column_id = await get_first_column_id(client, board["public_id"], headers)

    create_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=headers,
        json={"title": "Listed task"},
    )
    assert create_response.status_code == 200

    response = await client.get(
        f"/api/columns/{column_id}/cards",
        headers=headers,
    )

    assert response.status_code == 200

    cards = response.json()

    assert len(cards) == 1
    assert cards[0]["title"] == "Listed task"
    assert cards[0]["position"] == 0


async def test_update_card(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="update_card_user",
        email="update_card@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)
    column_id = await get_first_column_id(client, board["public_id"], headers)

    create_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=headers,
        json={
            "title": "Old task",
            "description": "Old description",
        },
    )
    assert create_response.status_code == 200

    card_id = create_response.json()["public_id"]

    response = await client.patch(
        f"/api/cards/{card_id}",
        headers=headers,
        json={
            "title": "New task",
            "description": "New description",
        },
    )

    assert response.status_code == 200

    card = response.json()

    assert card["title"] == "New task"
    assert card["description"] == "New description"


async def test_delete_card(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="delete_card_user",
        email="delete_card@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)
    column_id = await get_first_column_id(client, board["public_id"], headers)

    create_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=headers,
        json={"title": "Temporary task"},
    )
    assert create_response.status_code == 200

    card_id = create_response.json()["public_id"]

    delete_response = await client.delete(
        f"/api/cards/{card_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    cards_response = await client.get(
        f"/api/columns/{column_id}/cards",
        headers=headers,
    )

    assert cards_response.status_code == 200

    card_ids = [card["public_id"] for card in cards_response.json()]
    assert card_id not in card_ids


async def test_cards_have_incrementing_positions(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="card_positions_user",
        email="card_positions@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)
    column_id = await get_first_column_id(client, board["public_id"], headers)

    first_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=headers,
        json={"title": "First card"},
    )
    assert first_response.status_code == 200

    second_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=headers,
        json={"title": "Second card"},
    )
    assert second_response.status_code == 200

    response = await client.get(
        f"/api/columns/{column_id}/cards",
        headers=headers,
    )
    assert response.status_code == 200

    cards = response.json()

    assert len(cards) == 2
    assert [card["title"] for card in cards] == ["First card", "Second card"]
    assert [card["position"] for card in cards] == [0, 1]


async def test_other_user_cannot_delete_card_on_private_board(client: AsyncClient):
    owner_token = await register_and_get_token(
        client,
        username="card_owner",
        email="card_owner@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    column_id = await get_first_column_id(client, board["public_id"], owner_headers)

    create_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=owner_headers,
        json={"title": "Owner card"},
    )
    assert create_response.status_code == 200

    card_id = create_response.json()["public_id"]

    other_token = await register_and_get_token(
        client,
        username="card_other",
        email="card_other@example.com",
    )

    response = await client.delete(
        f"/api/cards/{card_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


async def test_other_user_cannot_update_card_on_private_board(client: AsyncClient):
    owner_token = await register_and_get_token(
        client,
        username="card_update_owner",
        email="card_update_owner@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    column_id = await get_first_column_id(client, board["public_id"], owner_headers)

    create_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=owner_headers,
        json={"title": "Owner card"},
    )
    assert create_response.status_code == 200

    card_id = create_response.json()["public_id"]

    other_token = await register_and_get_token(
        client,
        username="card_update_other",
        email="card_update_other@example.com",
    )

    response = await client.patch(
        f"/api/cards/{card_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"title": "Hacked title"},
    )

    assert response.status_code == 403


async def test_move_card_to_another_column(client: AsyncClient):
    token = await register_and_get_token(
        client,
        username="move_card_user",
        email="move_card@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    board = await create_board(client, token)
    board_id = board["public_id"]

    columns_response = await client.get(
        f"/api/boards/{board_id}/columns",
        headers=headers,
    )
    assert columns_response.status_code == 200

    columns = columns_response.json()
    first_column_id = columns[0]["public_id"]
    second_column_id = columns[1]["public_id"]

    create_response = await client.post(
        f"/api/columns/{first_column_id}/cards",
        headers=headers,
        json={"title": "Movable card"},
    )
    assert create_response.status_code == 200

    card_id = create_response.json()["public_id"]

    move_response = await client.patch(
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

    assert move_response.status_code == 200

    first_cards_response = await client.get(
        f"/api/columns/{first_column_id}/cards",
        headers=headers,
    )
    assert first_cards_response.status_code == 200
    assert first_cards_response.json() == []

    second_cards_response = await client.get(
        f"/api/columns/{second_column_id}/cards",
        headers=headers,
    )
    assert second_cards_response.status_code == 200

    cards = second_cards_response.json()
    assert len(cards) == 1
    assert cards[0]["public_id"] == card_id
    assert cards[0]["position"] == 0
