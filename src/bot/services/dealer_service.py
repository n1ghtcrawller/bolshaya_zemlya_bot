from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.dealer_profile import DealerProfile
from bot.db.repositories.dealer_profile import DealerProfileRepository


class DealerService:
    def __init__(self, session: AsyncSession) -> None:
        self._profiles = DealerProfileRepository(session)

    async def get_profile(self, user_id: int) -> DealerProfile | None:
        return await self._profiles.get_by_user_id(user_id)

    async def update_fields(self, user_id: int, fields: dict[str, Any]) -> DealerProfile:
        return await self._profiles.update_fields(user_id=user_id, fields=fields)
