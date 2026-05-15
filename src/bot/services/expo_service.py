from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.expo import Expo
from bot.db.repositories.expo import ExpoRepository


class ExpoService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ExpoRepository(session)

    async def list_upcoming(self) -> Sequence[Expo]:
        return await self._repo.list_upcoming(now=datetime.now(tz=timezone.utc))

    async def list_all(self) -> Sequence[Expo]:
        return await self._repo.list_all()

    async def get(self, expo_id: int) -> Expo | None:
        return await self._repo.get_by_id(expo_id)

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
        return await self._repo.create(
            title=title,
            location=location,
            description=description,
            products=products,
            starts_at=starts_at,
            ends_at=ends_at,
            created_by_user_id=created_by_user_id,
        )
