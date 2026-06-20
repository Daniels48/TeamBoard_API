from app.core.exceptions.exceptions import AppException
from app.infrastructure.db.models import Board, User
from app.infrastructure.db.models import BoardMember
from app.infrastructure.db.models.user import UserRole
from app.permissions.enums import BoardPermission


class BoardRBAC:
    @staticmethod
    def get_member(board: Board, user: User) -> BoardMember | None:
        return next((m for m in board.members if m.user_id == user.id),None,)

    @staticmethod
    def get_role(board: Board, user: User):

        if user.role == UserRole.ADMIN:
            return "admin"

        if board.owner_id == user.id:
            return "owner"

        member = BoardRBAC.get_member(board, user)

        if member:
            return member.role

        return None

    @staticmethod
    def check_permission(board: Board, user: User, permission: BoardPermission):
        role = BoardRBAC.get_role(board, user)


        if permission == BoardPermission.VIEW:
            allowed = role in ("admin","owner","editor","viewer")

        elif permission == BoardPermission.EDIT:
            allowed = role in ("admin","owner","editor",)

        elif permission == BoardPermission.MANAGE_MEMBERS:
            allowed = role in ("admin", "owner")

        else:
            allowed = False

        if not allowed:
            raise AppException("Forbidden", 403)