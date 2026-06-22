from httpx import AsyncClient

from tests.test_boards import register_and_get_token
from tests.test_columns import create_board


async def register_user(
    client: AsyncClient,
    *,
    username: str,
    email: str,
) -> str:
    return await register_and_get_token(
        client,
        username=username,
        email=email,
    )


async def test_owner_can_add_editor_member(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="member_owner",
        email="member_owner@example.com",
    )
    await verified_user("member_owner@example.com")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)

    await register_user(
        client,
        username="member_editor",
        email="member_editor@example.com",
    )

    response = await client.post(
        f"/api/members/{board['public_id']}",
        headers=owner_headers,
        json={
            "username": "member_editor",
            "role": "editor",
        },
    )

    assert response.status_code == 200

    member = response.json()
    assert member["username"] == "member_editor"
    assert member["role"] == "editor"


async def test_editor_can_see_shared_board(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="shared_owner",
        email="shared_owner@example.com",
    )
    await verified_user("shared_owner@example.com")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)

    editor_token = await register_user(
        client,
        username="shared_editor",
        email="shared_editor@example.com",
    )

    add_response = await client.post(
        f"/api/members/{board['public_id']}",
        headers=owner_headers,
        json={
            "username": "shared_editor",
            "role": "editor",
        },
    )
    assert add_response.status_code == 200

    boards_response = await client.get(
        "/api/boards",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert boards_response.status_code == 200

    boards = boards_response.json()

    shared_board = next(board_item for board_item in boards if board_item["public_id"] == board["public_id"])

    assert shared_board["title"] == board["title"]
    assert shared_board["role"] == "EDITOR"


async def test_editor_can_create_card_on_shared_board(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="editor_card_owner",
        email="editor_card_owner@example.com",
    )
    await verified_user("editor_card_owner@example.com")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    board_id = board["public_id"]

    editor_token = await register_user(
        client,
        username="editor_card_user",
        email="editor_card_user@example.com",
    )
    await verified_user("editor_card_user@example.com")
    editor_headers = {"Authorization": f"Bearer {editor_token}"}

    add_response = await client.post(
        f"/api/members/{board_id}",
        headers=owner_headers,
        json={
            "username": "editor_card_user",
            "role": "editor",
        },
    )
    assert add_response.status_code == 200

    columns_response = await client.get(
        f"/api/boards/{board_id}/columns",
        headers=editor_headers,
    )
    assert columns_response.status_code == 200

    column_id = columns_response.json()[0]["public_id"]

    create_response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=editor_headers,
        json={
            "title": "Editor task",
            "description": "Created by editor",
        },
    )

    assert create_response.status_code == 200
    assert create_response.json()["title"] == "Editor task"


async def test_viewer_cannot_create_card_on_shared_board(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="viewer_card_owner",
        email="viewer_card_owner@example.com",
    )
    await verified_user("viewer_card_owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    board_id = board["public_id"]

    viewer_token = await register_user(
        client,
        username="viewer_card_user",
        email="viewer_card_user@example.com",
    )
    await verified_user("viewer_card_user@example.com")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    add_response = await client.post(
        f"/api/members/{board_id}",
        headers=owner_headers,
        json={
            "username": "viewer_card_user",
            "role": "viewer",
        },
    )
    assert add_response.status_code == 200

    columns_response = await client.get(
        f"/api/boards/{board_id}/columns",
        headers=viewer_headers,
    )
    assert columns_response.status_code == 200

    column_id = columns_response.json()[0]["public_id"]

    response = await client.post(
        f"/api/columns/{column_id}/cards",
        headers=viewer_headers,
        json={"title": "Viewer cannot create"},
    )

    assert response.status_code == 403


async def test_owner_can_get_board_members(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="members_list_owner",
        email="members_list_owner@example.com",
    )
    await verified_user("members_list_owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    board_id = board["public_id"]

    await register_user(
        client,
        username="members_list_editor",
        email="members_list_editor@example.com",
    )

    add_response = await client.post(
        f"/api/members/{board_id}",
        headers=owner_headers,
        json={
            "username": "members_list_editor",
            "role": "editor",
        },
    )
    assert add_response.status_code == 200

    response = await client.get(
        f"/api/members/{board_id}",
        headers=owner_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["owner"]["username"] == "members_list_owner"
    assert len(data["members"]) == 1
    assert data["members"][0]["username"] == "members_list_editor"
    assert data["members"][0]["role"] == "editor"


async def test_owner_can_change_member_role(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="role_owner",
        email="role_owner@example.com",
    )
    await verified_user("role_owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    board_id = board["public_id"]

    await register_user(
        client,
        username="role_member",
        email="role_member@example.com",
    )

    add_response = await client.post(
        f"/api/members/{board_id}",
        headers=owner_headers,
        json={
            "username": "role_member",
            "role": "editor",
        },
    )
    assert add_response.status_code == 200
    assert add_response.json()["role"] == "editor"

    update_response = await client.patch(
        f"/api/members/{board_id}/role_member",
        headers=owner_headers,
        json={
            "role": "viewer",
        },
    )

    assert update_response.status_code == 200

    updated_member = update_response.json()
    assert updated_member["username"] == "role_member"
    assert updated_member["role"] == "viewer"

    members_response = await client.get(
        f"/api/members/{board_id}",
        headers=owner_headers,
    )

    assert members_response.status_code == 200

    members = members_response.json()["members"]

    member = next(item for item in members if item["username"] == "role_member")
    assert member["role"] == "viewer"


async def test_owner_can_remove_member_and_member_loses_access(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="remove_member_owner",
        email="remove_member_owner@example.com",
    )
    await verified_user("remove_member_owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    board_id = board["public_id"]

    member_token = await register_user(
        client,
        username="remove_member_user",
        email="remove_member_user@example.com",
    )
    await verified_user("remove_member_user@example.com")
    member_headers = {"Authorization": f"Bearer {member_token}"}

    add_response = await client.post(
        f"/api/members/{board_id}",
        headers=owner_headers,
        json={
            "username": "remove_member_user",
            "role": "editor",
        },
    )
    assert add_response.status_code == 200

    # До удаления участник видит доску.
    before_delete_response = await client.get(
        f"/api/boards/{board_id}",
        headers=member_headers,
    )
    assert before_delete_response.status_code == 200

    delete_response = await client.delete(
        f"/api/members/{board_id}/remove_member_user",
        headers=owner_headers,
    )
    assert delete_response.status_code == 204

    # После удаления доступа больше нет.
    after_delete_response = await client.get(
        f"/api/boards/{board_id}",
        headers=member_headers,
    )

    assert after_delete_response.status_code == 403


async def test_editor_cannot_add_member(
    client: AsyncClient,
    verified_user,
):
    owner_token = await register_user(
        client,
        username="add_member_owner",
        email="add_member_owner@example.com",
    )
    await verified_user("add_member_owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    board = await create_board(client, owner_token)
    board_id = board["public_id"]

    editor_token = await register_user(
        client,
        username="add_member_editor",
        email="add_member_editor@example.com",
    )
    await verified_user("add_member_editor@example.com")
    editor_headers = {"Authorization": f"Bearer {editor_token}"}

    await register_user(
        client,
        username="add_member_target",
        email="add_member_target@example.com",
    )

    add_editor_response = await client.post(
        f"/api/members/{board_id}",
        headers=owner_headers,
        json={
            "username": "add_member_editor",
            "role": "editor",
        },
    )
    assert add_editor_response.status_code == 200

    response = await client.post(
        f"/api/members/{board_id}",
        headers=editor_headers,
        json={
            "username": "add_member_target",
            "role": "viewer",
        },
    )

    assert response.status_code == 403
