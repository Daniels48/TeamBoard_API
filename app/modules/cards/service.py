from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import AppException
from app.infrastructure.db.models import Card, User
from app.modules.boards.board_repository import BoardRepository
from app.modules.cards.card_repository import CardRepository
from app.modules.cards.schema import CardCreate, CardUpdate
from app.modules.columns.column_repository import BoardColumnRepository
from app.permissions.board_permissions import BoardRBAC
from app.permissions.enums import BoardPermission


class CardService:
    @staticmethod
    async def create_card(db: AsyncSession, column_public_id: UUID, user: User, data: CardCreate) -> Card:
        column = await BoardColumnRepository.get_by_public_id(db=db, public_id=column_public_id)

        if not column:
            raise AppException("Column not found", 404)

        board = column.board

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.EDIT)

        cards = await CardRepository.get_by_column_id(db=db, column_id=column.id)

        card = Card(column_id=column.id, title=data.title, description=data.description, position=len(cards))

        card = await CardRepository.create(db=db, card=card)

        await db.commit()

        return card

    @staticmethod
    async def get_cards(
        db: AsyncSession,
        column_public_id: UUID,
        user: User,
    ) -> list[Card]:
        column = await BoardColumnRepository.get_by_public_id(db=db, public_id=column_public_id)

        if not column:
            raise AppException("Column not found", 404)

        board = column.board

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.VIEW)

        return await CardRepository.get_by_column_id(db=db, column_id=column.id)

    @staticmethod
    async def update_card(db: AsyncSession, card_public_id: UUID, user: User, data: CardUpdate) -> Card:

        card = await CardRepository.get_by_public_id(db=db, public_id=card_public_id)

        if not card:
            raise AppException("Card not found", 404)

        column = await BoardColumnRepository.get_by_id(db=db, column_id=card.column_id)

        board = await BoardRepository.get_by_id(db=db, board_id=column.board_id)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.EDIT)

        if data.title is not None:
            card.title = data.title

        if data.description is not None:
            card.description = data.description

        await db.commit()
        await db.refresh(card)

        return card

    @staticmethod
    async def delete_card(db: AsyncSession, card_public_id: UUID, user: User) -> None:
        card = await CardRepository.get_by_public_id(db=db, public_id=card_public_id)

        if not card:
            raise AppException("Card not found", 404)

        column = await BoardColumnRepository.get_by_id(db=db, column_id=card.column_id)

        board = await BoardRepository.get_by_id(db=db, board_id=column.board_id)

        BoardRBAC.check_permission(board=board, user=user, permission=BoardPermission.EDIT)

        await CardRepository.delete(db=db, card=card)

        await db.commit()
