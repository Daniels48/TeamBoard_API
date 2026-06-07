from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Card


class CardRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        card: Card,
    ) -> Card:

        db.add(card)

        await db.flush()
        await db.refresh(card)

        return card

    @staticmethod
    async def get_by_column_id(
        db: AsyncSession,
        column_id: int,
    ) -> list[Card]:

        stmt = (
            select(Card)
            .where(
                Card.column_id == column_id,
                Card.deleted_at.is_(None)
            )
            .order_by(Card.position)
        )

        result = await db.execute(stmt)

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def get_by_public_id(
        db: AsyncSession,
        public_id,
    ) -> Card | None:

        stmt = (
            select(Card)
            .where(
                Card.public_id == public_id,
                Card.deleted_at.is_(None)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def delete(
            db: AsyncSession,
            card: Card,
    ) -> None:
        card.deleted_at = datetime.now(timezone.utc)

        await db.flush()