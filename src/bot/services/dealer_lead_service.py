from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import RequestStatus
from bot.db.models.client_request import ClientRequest
from bot.db.repositories.client_request import ClientRequestRepository
from bot.logger import get_logger
from bot.schemas.dealer import DealerStats

log = get_logger(__name__)

ACTIVE_LEAD_STATUSES = (RequestStatus.TRANSFERRED_TO_DEALER, RequestStatus.IN_PROGRESS)


class DealerLeadService:
    """Лиды глазами Диллера: список, открытие, смена статуса, агрегаты."""

    def __init__(self, session: AsyncSession) -> None:
        self._requests = ClientRequestRepository(session)

    async def list_active(self, dealer_user_id: int) -> Sequence[ClientRequest]:
        return await self._requests.list_by_dealer(
            dealer_user_id, statuses=list(ACTIVE_LEAD_STATUSES)
        )

    async def list_all(self, dealer_user_id: int) -> Sequence[ClientRequest]:
        return await self._requests.list_by_dealer(dealer_user_id)

    async def get_for_dealer(
        self, dealer_user_id: int, request_id: int
    ) -> ClientRequest | None:
        request = await self._requests.get_by_id(request_id)
        if request is None or request.assigned_dealer_id != dealer_user_id:
            return None
        return request

    async def take_in_progress(
        self, dealer_user_id: int, request_id: int
    ) -> ClientRequest | None:
        request = await self.get_for_dealer(dealer_user_id, request_id)
        if request is None:
            return None
        if request.status not in ACTIVE_LEAD_STATUSES:
            return request
        return await self._requests.update_status(request, RequestStatus.IN_PROGRESS)

    async def mark_done(self, dealer_user_id: int, request_id: int) -> ClientRequest | None:
        request = await self.get_for_dealer(dealer_user_id, request_id)
        if request is None:
            return None
        return await self._requests.update_status(request, RequestStatus.DONE)

    async def mark_rejected(
        self, dealer_user_id: int, request_id: int
    ) -> ClientRequest | None:
        request = await self.get_for_dealer(dealer_user_id, request_id)
        if request is None:
            return None
        return await self._requests.update_status(request, RequestStatus.REJECTED)

    async def stats(self, dealer_user_id: int) -> DealerStats:
        grouped = await self._requests.count_by_dealer_grouped(dealer_user_id)
        return DealerStats(
            total=sum(grouped.values()),
            new=grouped.get(RequestStatus.TRANSFERRED_TO_DEALER, 0),
            in_progress=grouped.get(RequestStatus.IN_PROGRESS, 0),
            done=grouped.get(RequestStatus.DONE, 0),
            rejected=grouped.get(RequestStatus.REJECTED, 0),
        )
