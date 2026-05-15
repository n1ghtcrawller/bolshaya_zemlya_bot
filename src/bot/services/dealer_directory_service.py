from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.dealer_profile import DealerProfile
from bot.db.models.user import User
from bot.db.repositories.dealer_directory import DealerDirectoryRepository


class DealerDirectoryService:
    """Справочник дилеров: используется Sales для назначения и Клиентом для поиска."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = DealerDirectoryRepository(session)

    async def list_regions(self) -> Sequence[str]:
        return await self._repo.list_regions()

    async def list_by_region(self, region: str) -> Sequence[tuple[User, DealerProfile]]:
        return await self._repo.list_by_region(region)

    async def get_dealer(self, dealer_user_id: int) -> tuple[User, DealerProfile | None] | None:
        return await self._repo.get_dealer(dealer_user_id)
