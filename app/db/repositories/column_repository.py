from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import BoardColumn


class BoardColumnRepository:

    @staticmethod
    async def create(db: AsyncSession,column: BoardColumn) -> BoardColumn:
        db.add(column)
        await db.flush()
        await db.refresh(column)
        return column


    @staticmethod
    async def get_by_board_id(db: AsyncSession, board_id: int) -> list[BoardColumn]:
        stmt = (
            select(BoardColumn)
            .where(
                BoardColumn.board_id == board_id,
                BoardColumn.deleted_at.is_(None)
            )
            .order_by(
                BoardColumn.position
            )
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_public_id(db: AsyncSession, public_id: UUID) -> BoardColumn | None:
        stmt = (
            select(BoardColumn)
            .options(
                selectinload(BoardColumn.board)
            )
            .where(
                BoardColumn.public_id == public_id,
                BoardColumn.deleted_at.is_(None)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_public_ids(db: AsyncSession, public_ids: list[UUID]) -> list[BoardColumn]:
        stmt = (
            select(BoardColumn)
            .where(
                BoardColumn.public_id.in_(public_ids),
                BoardColumn.deleted_at.is_(None),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, column_id: int) -> BoardColumn | None:

        stmt = (
            select(BoardColumn)
            .where(
                BoardColumn.id == column_id,
                BoardColumn.deleted_at.is_(None)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()