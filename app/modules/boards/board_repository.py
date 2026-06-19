from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, func, case, and_, or_, cast, literal, String
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from app.modules.boards.schema import BoardResponse
from app.infrastructure.db.models import Board, BoardColumn, Card, BoardMember, User

Owner = aliased(User)


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
    async def get_all_boards(db: AsyncSession) -> list[BoardResponse]:
        stmt = (
            select(
                Board.public_id,
                Board.title,
                Board.description,
                Board.created_at,
                Board.updated_at,

                Owner.username.label("owner_username"),

                literal("admin").label("role"),

                func.count(
                    func.distinct(BoardColumn.id)
                ).label("columns_count"),

                func.count(
                    func.distinct(Card.id)
                ).label("cards_count"),
            )
            .join(
                Owner,
                Owner.id == Board.owner_id,
            )
            .outerjoin(
                BoardColumn,
                and_(
                    BoardColumn.board_id == Board.id,
                    BoardColumn.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                Card,
                and_(
                    Card.column_id == BoardColumn.id,
                    Card.deleted_at.is_(None),
                ),
            )
            .where(
                Board.deleted_at.is_(None),
            )
            .group_by(
                Board.id,
                Board.public_id,
                Board.title,
                Board.description,
                Board.created_at,
                Board.updated_at,
                Owner.username,
            )
            .order_by(Board.created_at.desc())
        )

        result = await db.execute(stmt)

        return [
            BoardResponse(
                public_id=row.public_id,
                title=row.title,
                description=row.description,
                created_at=row.created_at,
                updated_at=row.updated_at,

                owner_username=row.owner_username,
                role=row.role,

                columns_count=row.columns_count,
                cards_count=row.cards_count,
            )
            for row in result.all()
        ]

    @staticmethod
    async def get_users_boards(db: AsyncSession, user_id: int) -> list[BoardResponse]:
        stmt = (
            select(
                Board.public_id,
                Board.title,
                Board.description,
                Board.created_at,
                Board.updated_at,
                Owner.username.label("owner_username"),
                case(
                    (
                        Board.owner_id == user_id,
                        literal("owner"),
                    ),else_=cast(BoardMember.role, String),
                ).label("role"),
                func.count(func.distinct(BoardColumn.id)).label("columns_count"),
                func.count(func.distinct(Card.id)).label("cards_count"),
            )
            .join(Owner, Owner.id == Board.owner_id)
            .outerjoin(
                BoardMember,
                and_(
                    BoardMember.board_id == Board.id,
                    BoardMember.user_id == user_id,
                ),
            )
            .outerjoin(
                BoardColumn,
                and_(
                    BoardColumn.board_id == Board.id,
                    BoardColumn.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                Card,
                and_(
                    Card.column_id == BoardColumn.id,
                    Card.deleted_at.is_(None),
                ),
            )
            .where(
                Board.deleted_at.is_(None),
                or_(
                    Board.owner_id == user_id,
                    BoardMember.user_id == user_id,
                ),
            )
            .group_by(
                Board.id,
                Board.public_id,
                Board.title,
                Board.description,
                Board.created_at,
                Board.updated_at,
                Owner.username,
                Board.owner_id,
                BoardMember.role,
            )
            .order_by(Board.created_at.desc())
        )

        result = await db.execute(stmt)

        rows = result.all()

        return [
            BoardResponse(
                public_id=row.public_id,
                title=row.title,
                description=row.description,
                created_at=row.created_at,
                updated_at=row.updated_at,

                owner_username=row.owner_username,
                role=row.role,

                columns_count=row.columns_count,
                cards_count=row.cards_count,
            )
            for row in rows
        ]

    @staticmethod
    async def get_by_public_id(db: AsyncSession, public_id: UUID) -> Board | None:
        stmt = (
            select(Board)
            .options(
                selectinload(Board.members)
            )
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


