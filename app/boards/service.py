from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.boards.schema import BoardCreate, BoardFullResponse
from app.cards.schema import BoardLayoutUpdate
from app.core.Exceptions.exceptions import AppException
from app.db.models import User, Board, BoardColumn
from app.db.models.user import UserRole
from app.db.repositories.board_repository import BoardRepository
from app.db.repositories.card_repository import CardRepository
from app.db.repositories.column_repository import BoardColumnRepository
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
        board = Board(owner_id=user.id,title=data.title,description=data.description,is_public=data.is_public)
        board = await BoardRepository.create(db=db,board=board,)

        for position, title  in enumerate(DEFAULT_COLUMNS):
            column = BoardColumn(board_id=board.id,title=title,position=position)
            await BoardColumnRepository.create(db=db,column=column,)

        await db.commit()

        return board

    @staticmethod
    async def get_my_boards(db: AsyncSession, user: User) -> list[Board]:
        if user.role == UserRole.ADMIN:
            return await BoardRepository.get_all(db=db)

        return await BoardRepository.get_users_boards(db=db,user_id=user.id)

    @staticmethod
    async def get_board(db: AsyncSession, public_id: UUID,user: User) -> Board:

        board = await BoardRepository.get_by_public_id(db=db,public_id=public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.VIEW)

        return board

    @staticmethod
    async def get_full_board(db: AsyncSession, public_id: UUID, user: User) -> BoardFullResponse:
        board = await BoardRepository.get_full_by_public_id(db=db,public_id=public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.VIEW)

        response = BoardFullResponse.model_validate(board)
        response.board_role = BoardRBAC.get_role(board=board, user=user)
        return response

    @staticmethod
    async def update_layout(db: AsyncSession, board_public_id: UUID, user: User, data: BoardLayoutUpdate):
        board = await BoardRepository.get_by_public_id(db=db, public_id=board_public_id)

        if not board:
            raise AppException("Board not found",404)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.EDIT)

        for item in data.cards:
            card = await CardRepository.get_by_public_id(db=db,public_id=item.card_id)
            column = await BoardColumnRepository.get_by_public_id(db=db, public_id=item.column_id)
            if not card or not column:
                continue

            card.column_id = column.id
            card.position = item.position

        await db.commit()
