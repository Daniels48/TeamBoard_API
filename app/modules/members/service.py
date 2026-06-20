from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import AppException
from app.infrastructure.db.models import User, BoardMember
from app.infrastructure.db.models.board_member import BoardRole
from app.modules.boards.board_repository import BoardRepository
from app.modules.members.member_rerositoriy import BoardMemberRepository
from app.modules.users.service import UserPolicy
from app.modules.users.user_repository import UserRepository
from app.modules.members.schema import AddBoardMemberRequest, BoardMemberResponse, BoardMembersResponse, BoardOwnerResponse
from app.permissions.board_permissions import BoardRBAC
from app.permissions.enums import BoardPermission


class BoardMemberService:

    @staticmethod
    async def add_member(db: AsyncSession, board_public_id: UUID, current_user: User,data: AddBoardMemberRequest)-> BoardMemberResponse:
        UserPolicy.require_verified_email(user=current_user)

        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found", 404)

        BoardRBAC.check_permission(board=board, user=current_user, permission=BoardPermission.MANAGE_MEMBERS)

        target_user = await UserRepository.get_by_username(db=db, username=data.username)

        if not target_user:
            raise AppException("User not found", 404)

        if target_user.id == board.owner_id:
            raise AppException("Owner is already a member",400,)

        exists = await BoardMemberRepository.get_member(db=db,board_id=board.id,user_id=target_user.id)

        if exists:
            raise AppException("User already added",400)

        member = BoardMember(board_id=board.id,user_id=target_user.id,role=data.role)

        await BoardMemberRepository.create(db=db, member=member)

        await db.commit()

        return BoardMemberResponse(username=target_user.username, role=member.role)

    @staticmethod
    async def get_members(db: AsyncSession, board_public_id: UUID, current_user: User) -> BoardMembersResponse:
        board = await BoardRepository.get_board_members(db=db, public_id=board_public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=current_user, permission=BoardPermission.MANAGE_MEMBERS)

        owner = BoardOwnerResponse(username=board.owner.username)
        members = [BoardMemberResponse(username=m.user.username,role=m.role) for m in board.members]

        return BoardMembersResponse(owner=owner, members=members)

    @staticmethod
    async def delete_member(db: AsyncSession, board_public_id: UUID, username: str, current_user: User):
        UserPolicy.require_verified_email(user=current_user)
        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found", 404)

        BoardRBAC.check_permission(board=board, user=current_user, permission=BoardPermission.MANAGE_MEMBERS)

        target_user = await UserRepository.get_by_username(db=db,username=username)

        if not target_user:
            raise AppException("User not found", 404)

        if target_user.id == board.owner_id:
            raise AppException("Owner cannot be removed",400,)

        member = await BoardMemberRepository.get_member(db=db,board_id=board.id,user_id=target_user.id)

        if not member:
            raise AppException("Member not found", 404)

        await BoardMemberRepository.delete_member(db=db, user_id=target_user.id, board_id=board.id)
        await db.commit()

    @staticmethod
    async def update_role(db: AsyncSession, board_public_id: UUID, username: str, role: BoardRole, current_user: User) -> BoardMemberResponse:
        UserPolicy.require_verified_email(user=current_user)
        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found", 404)


        BoardRBAC.check_permission(board=board, user=current_user, permission=BoardPermission.MANAGE_MEMBERS)

        target_user = await UserRepository.get_by_username(db=db,username=username,)

        if not target_user:
            raise AppException("User not found", 404)

        if target_user.id == board.owner_id:
            raise AppException("Owner role cannot be changed",400)

        member = await BoardMemberRepository.get_member(db=db,board_id=board.id,user_id=target_user.id)

        if not member:
            raise AppException("Member not found", 404)

        member.role = role

        await db.commit()

        return BoardMemberResponse(username=target_user.username, role=member.role)