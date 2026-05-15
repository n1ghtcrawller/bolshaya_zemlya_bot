from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import UserRole
from bot.db.models.dealer_profile import DealerProfile
from bot.db.models.user import User


class DealerDirectoryRepository:
    """Справочник активных дилеров для назначения лидов и публичного поиска."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_regions(self) -> Sequence[str]:
        stmt = (
            select(DealerProfile.region)
            .join(User, User.id == DealerProfile.user_id)
            .where(
                User.role == UserRole.DEALER,
                User.is_active.is_(True),
                DealerProfile.region.is_not(None),
            )
            .distinct()
            .order_by(DealerProfile.region.asc())
        )
        result = await self._session.scalars(stmt)
        return [r for r in result.all() if r]

    async def list_by_region(self, region: str) -> Sequence[tuple[User, DealerProfile]]:
        stmt = (
            select(User, DealerProfile)
            .join(DealerProfile, DealerProfile.user_id == User.id)
            .where(
                User.role == UserRole.DEALER,
                User.is_active.is_(True),
                DealerProfile.region == region,
            )
            .order_by(User.full_name.asc())
        )
        result = await self._session.execute(stmt)
        return [(u, p) for u, p in result.all()]

    async def get_dealer(self, dealer_user_id: int) -> tuple[User, DealerProfile | None] | None:
        stmt = (
            select(User, DealerProfile)
            .outerjoin(DealerProfile, DealerProfile.user_id == User.id)
            .where(User.id == dealer_user_id, User.role == UserRole.DEALER)
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return row[0], row[1]
