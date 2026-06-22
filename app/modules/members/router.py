from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DBSession
from app.modules.members.schema import (
    AddBoardMemberRequest,
    BoardMemberResponse,
    BoardMembersResponse,
    UpdateMemberRoleRequest,
)
from app.modules.members.service import BoardMemberService

router_board_members = APIRouter(prefix="/members", tags=["Board Members"])


@router_board_members.post("/{board_id}", response_model=BoardMemberResponse)
async def add_member(board_id: UUID, data: AddBoardMemberRequest, db: DBSession, user: CurrentUser):
    return await BoardMemberService.add_member(db=db, board_public_id=board_id, current_user=user, data=data)


@router_board_members.get("/{board_id}", response_model=BoardMembersResponse)
async def get_members(board_id: UUID, db: DBSession, user: CurrentUser):
    return await BoardMemberService.get_members(db=db, board_public_id=board_id, current_user=user)


@router_board_members.delete("/{board_id}/{username}", status_code=204)
async def delete_member(board_id: UUID, username: str, db: DBSession, current_user: CurrentUser):
    await BoardMemberService.delete_member(
        db=db, board_public_id=board_id, username=username, current_user=current_user
    )


@router_board_members.patch("/{board_id}/{username}", response_model=BoardMemberResponse)
async def update_member_role(
    board_id: UUID, username: str, data: UpdateMemberRoleRequest, db: DBSession, current_user: CurrentUser
):
    return await BoardMemberService.update_role(
        db=db, board_public_id=board_id, username=username, role=data.role, current_user=current_user
    )
