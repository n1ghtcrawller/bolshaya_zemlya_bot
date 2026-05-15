from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.client_request import ClientRequestRepository
from bot.db.repositories.user import UserRepository
from bot.schemas.marketing import DashboardSnapshot


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)
        self._requests = ClientRequestRepository(session)

    async def snapshot(self) -> DashboardSnapshot:
        users_by_role = await self._users.count_by_role()
        leads_by_status = await self._requests.count_grouped()
        return DashboardSnapshot(
            users_by_role=users_by_role,
            leads_by_status=leads_by_status,
        )
