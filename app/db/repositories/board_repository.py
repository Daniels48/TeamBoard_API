from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from app.db.models import Board, BoardColumn, Card, BoardMember


def now_dt():
    return datetime.now(timezone.utc)


class BoardRepository:
    @staticmethod
    async def create(db: AsyncSession, board: Board) -> Board:
        db.add(board)
        await db.flush()
        await db.refresh(board)
        return board

    @staticmethod
    async def get_by_owner_id(db: AsyncSession,owner_id: int) -> list[Board]:
        stmt = (
            select(Board)
            .where(
                Board.owner_id == owner_id,
                Board.deleted_at.is_(None)
            )
            .order_by(Board.created_at.desc())
        )

        result = await db.execute(stmt)

        return list(result.scalars().all())

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Board]:
        stmt = (
            select(Board)
            .where(Board.deleted_at.is_(None))
            .order_by(Board.created_at.desc())
        )

        result = await db.execute(stmt)

        return list(result.scalars().all())

    @staticmethod
    async def get_users_boards(db: AsyncSession,user_id: int) -> list[Board]:
        stmt = (
            select(Board)
            .outerjoin(
                BoardMember,
                BoardMember.board_id == Board.id,
            )
            .where(
                or_(
                    Board.owner_id == user_id,
                    BoardMember.user_id == user_id,
                ),
                Board.deleted_at.is_(None),
            )
            .order_by(Board.created_at.desc())
            .distinct()
        )

        result = await db.execute(stmt)

        return list(result.scalars().all())


    @staticmethod
    async def get_by_public_id(db: AsyncSession, public_id: UUID) -> Board | None:
        stmt = (
            select(Board)
            .where(
                Board.public_id == public_id,
                Board.deleted_at.is_(None)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()


    @staticmethod
    async def get_board_members(db: AsyncSession, public_id: UUID) -> Board:
        stmt = (
            select(Board)
            .options(
                selectinload(Board.owner),
                selectinload(Board.members)
                .selectinload(BoardMember.user)
            )
            .where(
                Board.public_id == public_id
            )
        )
        result = await db.execute(stmt)

        return result.scalar_one_or_none()


    @staticmethod
    async def get_by_id(db: AsyncSession, board_id: int) -> Board | None:
        stmt = (
            select(Board)
            .where(
                Board.id == board_id,
                Board.deleted_at.is_(None)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_full_by_public_id(db: AsyncSession, public_id: UUID) -> Board | None:
        stmt = (
            select(Board)
            .options(
                selectinload(Board.owner),

                selectinload(Board.members)
                .selectinload(BoardMember.user),

                selectinload(Board.columns)
                .selectinload(BoardColumn.cards),

                with_loader_criteria(
                    BoardColumn,
                    BoardColumn.deleted_at.is_(None),
                    include_aliases=True,
                ),

                with_loader_criteria(
                    Card,
                    Card.deleted_at.is_(None),
                    include_aliases=True,
                ),
            )
            .where(
                Board.public_id == public_id,
                Board.deleted_at.is_(None),
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()


