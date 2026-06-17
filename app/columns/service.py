from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.columns.schema import BoardColumnCreate, BoardColumnUpdate, BoardColumnResponse
from app.core.Exceptions.exceptions import AppException
from app.db.models import BoardColumn, User
from app.db.repositories.board_repository import BoardRepository
from app.db.repositories.column_repository import BoardColumnRepository
from app.permissions.board_permissions import BoardRBAC
from app.permissions.enums import BoardPermission


class BoardColumnService:

    @staticmethod
    async def create_column(db: AsyncSession, board_public_id: UUID, user: User,data: BoardColumnCreate) -> BoardColumn:
        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found",404,)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.MANAGE_MEMBERS)

        columns = await BoardColumnRepository.get_by_board_id(db=db,board_id=board.id)

        column = BoardColumn(board_id=board.id, title=data.title, position=len(columns))

        column = await BoardColumnRepository.create(db=db, column=column)

        await db.commit()

        return column

    @staticmethod
    async def get_columns(db: AsyncSession, board_public_id: UUID, user: User) -> list[BoardColumn]:
        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.VIEW)

        return await BoardColumnRepository.get_by_board_id(db=db,board_id=board.id)

    @staticmethod
    async def update_column(
            db: AsyncSession,
            board_public_id: UUID,
            column_public_id: UUID,
            user: User,
            data: BoardColumnUpdate,
    ) -> BoardColumnResponse:

        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found", 404)

        BoardRBAC.check_permission(board=board,user=user,permission=BoardPermission.EDIT)

        column = await BoardColumnRepository.get_by_public_id(db=db,public_id=column_public_id)

        if not column:
            raise AppException("Column not found", 404)

        column.title = data.title

        await db.commit()
        await db.refresh(column)

        return BoardColumnResponse.model_validate(column)

    @staticmethod
    async def delete_column(db: AsyncSession,board_public_id: UUID,column_public_id: UUID,user: User,):
        board = await BoardRepository.get_by_public_id(db=db,public_id=board_public_id)

        if not board:
            raise AppException("Board not found", 404)

        BoardRBAC.check_permission(board=board,user=user,permission=BoardPermission.MANAGE_MEMBERS)

        column = await BoardColumnRepository.get_by_public_id(db=db,public_id=column_public_id)

        if not column:
            raise AppException("Column not found", 404)

        column.deleted_at = datetime.now(timezone.utc)

        await db.commit()