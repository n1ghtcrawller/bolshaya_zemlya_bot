from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import RequestStatus
from bot.db.models.client_request import ClientRequest
from bot.db.repositories.client_request import ClientRequestRepository
from bot.logger import get_logger

log = get_logger(__name__)


class SalesLeadService:
    """Лиды глазами Sales:
    - общая очередь NEW (без assigned_sales_id),
    - свои IN_PROGRESS,
    - свои TRANSFERRED_TO_DEALER.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._requests = ClientRequestRepository(session)

    async def list_new(self) -> Sequence[ClientRequest]:
        return await self._requests.list_unassigned()

    async def list_in_progress(self, sales_user_id: int) -> Sequence[ClientRequest]:
        return await self._requests.list_by_sales(
            sales_user_id, statuses=[RequestStatus.IN_PROGRESS]
        )

    async def list_transferred(self, sales_user_id: int) -> Sequence[ClientRequest]:
        return await self._requests.list_by_sales(
            sales_user_id, statuses=[RequestStatus.TRANSFERRED_TO_DEALER]
        )

    async def get(self, request_id: int) -> ClientRequest | None:
        return await self._requests.get_by_id(request_id)

    async def take(self, sales_user_id: int, request_id: int) -> ClientRequest | None:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            return None
        if request.status != RequestStatus.NEW or request.assigned_sales_id is not None:
            return request
        request = await self._requests.assign_sales(
            request, sales_user_id, RequestStatus.IN_PROGRESS
        )
        log.info("sales_lead_taken", request_id=request.id, sales_id=sales_user_id)
        return request

    async def transfer_to_dealer(
        self, sales_user_id: int, request_id: int, dealer_user_id: int
    ) -> ClientRequest | None:
        request = await self._requests.get_by_id(request_id)
        if request is None or request.assigned_sales_id != sales_user_id:
            return None
        request = await self._requests.assign_dealer(
            request, dealer_user_id, RequestStatus.TRANSFERRED_TO_DEALER
        )
        log.info(
            "sales_lead_transferred",
            request_id=request.id,
            sales_id=sales_user_id,
            dealer_id=dealer_user_id,
        )
        return request

    async def reject(self, sales_user_id: int, request_id: int) -> ClientRequest | None:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            return None
        owned = request.assigned_sales_id in (None, sales_user_id)
        if not owned:
            return None
        if request.assigned_sales_id is None:
            await self._requests.assign_sales(request, sales_user_id, RequestStatus.REJECTED)
        else:
            await self._requests.update_status(request, RequestStatus.REJECTED)
        return request

    async def keep(
        self, sales_user_id: int, request_id: int
    ) -> ClientRequest | None:
        """Sales решает оставить лид у себя — `kept_by_sales`. Дилер не назначается."""
        request = await self._requests.get_by_id(request_id)
        if request is None or request.assigned_sales_id != sales_user_id:
            return None
        request = await self._requests.update_status(request, RequestStatus.KEPT_BY_SALES)
        log.info("sales_lead_kept", request_id=request.id, sales_id=sales_user_id)
        return request

    async def list_kept(self, sales_user_id: int) -> Sequence[ClientRequest]:
        return await self._requests.list_by_sales(
            sales_user_id, statuses=[RequestStatus.KEPT_BY_SALES]
        )
