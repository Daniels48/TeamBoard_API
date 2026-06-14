from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import BoardMember, Board


class BoardMemberRepository:

    @staticmethod
    async def create(db: AsyncSession,member: BoardMember) -> BoardMember:
        db.add(member)
        await db.flush()
        return member

    @staticmethod
    async def get_board_members(db: AsyncSession, board_id: int) -> list[BoardMember]:
        stmt = (
            select(BoardMember)
            .options(selectinload(BoardMember.user), selectinload(Board.owner))
            .where(BoardMember.board_id == board_id)
        )

        result = await db.execute(stmt)

        return list(result.scalars().all())

    @staticmethod
    async def get_member(db: AsyncSession, board_id: int, user_id: int) -> BoardMember | None:

        stmt = (
            select(BoardMember)
            .where(
                BoardMember.board_id == board_id,
                BoardMember.user_id == user_id,
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    # @staticmethod
    # async def get_board_members(db: AsyncSession, board_id: int) -> list[BoardMember]:
    #     stmt = (
    #         select(BoardMember)
    #         .where(
    #             BoardMember.board_id == board_id,
    #         )
    #     )
    #     result = await db.execute(stmt)
    #     return list(result.scalars().all())

    @staticmethod
    async def delete_member(db: AsyncSession,board_id: int,user_id: int) -> None:
        stmt = (
            delete(BoardMember)
            .where(
                BoardMember.board_id == board_id,
                BoardMember.user_id == user_id,
            )
        )
        await db.execute(stmt)

