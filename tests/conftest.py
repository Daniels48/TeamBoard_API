from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.infrastructure.db.models  # noqa: F401
from app.core.config import settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import User
from app.infrastructure.db.models.user import UserRole
from app.infrastructure.redis.service import SessionCache
from app.main import app

test_engine = create_async_engine(
    settings.test_async_db_url,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def verified_user():
    async def _verified_user(email: str) -> None:
        async with TestSessionLocal() as session:
            await session.execute(
                update(User).where(User.email == email).values(email_verified_at=datetime.now(timezone.utc))
            )
            await session.commit()

    return _verified_user


@pytest.fixture
async def admin_user():
    async def _admin_user(email: str) -> None:
        async with TestSessionLocal() as session:
            await session.execute(update(User).where(User.email == email).values(role=UserRole.ADMIN))
            await session.commit()

    return _admin_user


@pytest.fixture(autouse=True)
def mock_redis_session_cache(monkeypatch):
    cache: dict[str, object] = {}

    async def fake_get(cls, session_id: str):
        return cache.get(session_id)

    async def fake_set(cls, session_id: str, data: object, ttl: int):
        cache[session_id] = data

    async def fake_delete(cls, session_id: str):
        cache.pop(session_id, None)

    monkeypatch.setattr(SessionCache, "get", classmethod(fake_get))
    monkeypatch.setattr(SessionCache, "set", classmethod(fake_set))
    monkeypatch.setattr(SessionCache, "delete", classmethod(fake_delete))


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.pop(get_db, None)
