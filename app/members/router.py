from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.members.schema import BoardMemberResponse, AddBoardMemberRequest, BoardMembersResponse, UpdateMemberRoleRequest
from app.members.service import BoardMemberService

router_board_members = APIRouter(prefix="/members",tags=["Board Members"])


@router_board_members.post("/{board_id}",response_model=BoardMemberResponse,)
async def add_member(
    board_id: UUID,
    data: AddBoardMemberRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await BoardMemberService.add_member(db=db,board_public_id=board_id, current_user=user, data=data)

@router_board_members.get("/{board_id}", response_model=BoardMembersResponse)
async def get_members(board_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await BoardMemberService.get_members(db=db, board_public_id=board_id, current_user=user)


@router_board_members.delete("/{board_id}/{username}",status_code=204)
async def delete_member(board_id: UUID,username: str,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)):
    await BoardMemberService.delete_member(db=db, board_public_id=board_id, username=username, current_user=current_user)


@router_board_members.patch("/{board_id}/{username}", response_model=BoardMemberResponse)
async def update_member_role(
    board_id: UUID,
    username: str,
    data: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await BoardMemberService.update_role(db=db,board_public_id=board_id, username=username, role=data.role, current_user=current_user)


