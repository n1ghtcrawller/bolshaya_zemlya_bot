from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.core.enums import UserRole
from bot.db import models  # noqa: F401  ensure all mappings registered
from bot.db.base import Base
from bot.db.models.user import User


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    @event.listens_for(eng.sync_engine, "connect")
    def _enable_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as s:
        yield s


@pytest.fixture
def make_user():
    """Фабрика User — telegram_id увеличивается автоматически, чтобы UNIQUE не падал."""
    seq = {"id": 1_000_000_000}

    def _factory(
        session: AsyncSession,
        *,
        role: UserRole = UserRole.CLIENT,
        full_name: str = "Test User",
        username: str | None = None,
        telegram_id: int | None = None,
        is_active: bool = True,
    ) -> User:
        if telegram_id is None:
            seq["id"] += 1
            telegram_id = seq["id"]
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=role,
            is_active=is_active,
        )
        session.add(user)
        return user

    return _factory
