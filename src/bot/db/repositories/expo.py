from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.expo import Expo


class ExpoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, expo_id: int) -> Expo | None:
        return await self._session.get(Expo, expo_id)

    async def list_upcoming(self, *, limit: int = 20, now: datetime) -> Sequence[Expo]:
        stmt = (
            select(Expo)
            .where(Expo.starts_at >= now)
            .order_by(Expo.starts_at.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_all(self, *, limit: int = 20) -> Sequence[Expo]:
        stmt = select(Expo).order_by(Expo.starts_at.desc()).limit(limit)
        return (await self._session.scalars(stmt)).all()

    async def create(
        self,
        *,
        title: str,
        location: str | None,
        description: str | None,
        products: str | None,
        starts_at: datetime,
        ends_at: datetime | None,
        created_by_user_id: int | None,
    ) -> Expo:
        expo = Expo(
            title=title,
            location=location,
            description=description,
            products=products,
            starts_at=starts_at,
            ends_at=ends_at,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(expo)
        await self._session.flush()
        return expo
