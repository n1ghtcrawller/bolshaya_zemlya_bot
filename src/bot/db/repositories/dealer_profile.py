from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.dealer_profile import DealerProfile

ALLOWED_FIELDS = frozenset({"phone", "company", "region", "address", "description"})


class DealerProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> DealerProfile | None:
        stmt = select(DealerProfile).where(DealerProfile.user_id == user_id)
        return await self._session.scalar(stmt)

    async def update_fields(self, *, user_id: int, fields: dict[str, Any]) -> DealerProfile:
        """Создаёт профиль если его нет; применяет только ключи из ``fields``.

        Передача ``None`` явно — очищает поле (отличается от ``upsert`` где None == "не трогать").
        """
        unknown = set(fields).difference(ALLOWED_FIELDS)
        if unknown:
            raise ValueError(f"unknown profile fields: {sorted(unknown)}")

        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = DealerProfile(user_id=user_id, **fields)
            self._session.add(profile)
        else:
            for key, value in fields.items():
                setattr(profile, key, value)
        await self._session.flush()
        return profile
