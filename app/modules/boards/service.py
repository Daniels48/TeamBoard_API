from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.modules.boards.schema import BoardCreate, BoardFullResponse, BoardResponse, BoardUpdate, BoardBaseResponse
from app.modules.cards.schema import BoardLayoutUpdate
from app.core.exceptions.exceptions import AppException
from app.infrastructure.db.models import User, Board, BoardColumn
from app.infrastructure.db.models.user import UserRole
from app.modules.boards.board_repository import BoardRepository
from app.modules.cards.card_repository import CardRepository
from app.modules.columns.column_repository import BoardColumnRepository
from app.permissions.board_permissions import BoardRBAC
from app.permissions.enums import BoardPermission

DEFAULT_COLUMNS = (
    "Todo",
    "In Progress",
    "Done",
)


class BoardService:

    @staticmethod
    async def create_board(db: AsyncSession,user: User,data: BoardCreate) -> Board:
        board = Board(owner_id=user.id,title=data.title,description=data.description)
        board = await BoardRepository.create(db=db,board=board)

        for position, title  in enumerate(DEFAULT_COLUMNS):
            column = BoardColumn(board_id=board.id,title=title,position=position)
            await BoardColumnRepository.create(db=db,column=column)

        await db.commit()

        return board

    @staticmethod
    async def get_accessible_boards(db: AsyncSession, user: User) -> list[BoardResponse]:
        if user.role == UserRole.ADMIN:
            return await BoardRepository.get_all_boards(db)

        return await BoardRepository.get_users_boards(db=db, user_id=user.id)

    @staticmethod
    async def get_board(db: AsyncSession, public_id: UUID, user: User) -> BoardFullResponse:
        board = await BoardRepository.get_full_by_public_id(db=db,public_id=public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.VIEW)

        response = BoardFullResponse.model_validate(board)
        response.board_role = BoardRBAC.get_role(board=board, user=user)
        response.owner_username = board.owner.username
        return response

    @staticmethod
    async def update_board(db: AsyncSession,public_id: UUID,user: User,data: BoardUpdate) -> BoardBaseResponse:
        board = await BoardRepository.get_by_public_id(db=db,public_id=public_id)

        if not board:
            raise AppException("Board not found", 404)

        BoardRBAC.check_permission(board=board,user=user,permission=BoardPermission.MANAGE_MEMBERS)

        if data.title is not None:
            board.title = data.title

        if data.description is not None:
            board.description = data.description

        await db.commit()
        await db.refresh(board)

        return BoardBaseResponse.model_validate(board)

    @staticmethod
    async def delete_board(db: AsyncSession,public_id: UUID,user: User) -> dict[str, str]:
        board = await BoardRepository.get_by_public_id(db=db, public_id=public_id,)

        if not board:
            raise AppException("Board not found", 404)

        BoardRBAC.check_permission(board=board,user=user, permission=BoardPermission.MANAGE_MEMBERS)

        board.deleted_at = datetime.now(timezone.utc)

        await db.commit()

        return {"message": "Board deleted"}

    @staticmethod
    async def update_layout(db: AsyncSession, board_public_id: UUID, user: User, data: BoardLayoutUpdate):
        board = await BoardRepository.get_by_public_id(db=db, public_id=board_public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.EDIT)

        card_ids = set()
        column_ids = set()

        for item in data.cards:
            card_ids.add(item.card_id)
            column_ids.add(item.column_id)

        cards = await CardRepository.get_by_public_ids(db=db,public_ids=list(card_ids))

        columns = await BoardColumnRepository.get_by_public_ids(db=db,public_ids=list(column_ids))

        cards_map = {card.public_id: card for card in cards}

        columns_map = {column.public_id: column for column in columns}

        for item in data.cards:
            card = cards_map.get(item.card_id)
            column = columns_map.get(item.column_id)

            if not card or not column:
                continue

            card.column_id = column.id
            card.position = item.position

        await db.commit()

        return {"message": "success"}
