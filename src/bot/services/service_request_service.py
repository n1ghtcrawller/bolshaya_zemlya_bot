from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import BitrixSettings
from bot.core.enums import BitrixLeadSource, ServiceIssueType, ServiceRequestStatus
from bot.db.models.service_request import ServiceRequest
from bot.db.models.user import User
from bot.db.repositories.bitrix_outbox import BitrixOutboxRepository
from bot.db.repositories.service_request import ServiceRequestRepository
from bot.logger import get_logger
from bot.schemas.request import ServiceRequestCreate
from bot.services.bitrix_lead_builder import normalize_service_request

log = get_logger(__name__)


class ServiceRequestService:
    """Сервисные обращения (гарантия / ремонт / запчасти).

    Создаёт Клиент. Дилер видит свои + общую очередь. Берёт в работу → закрывает.
    """

    def __init__(
        self, session: AsyncSession, bitrix_settings: BitrixSettings | None = None
    ) -> None:
        self._session = session
        self._repo = ServiceRequestRepository(session)
        self._outbox = BitrixOutboxRepository(session)
        self._bitrix_enabled = bool(bitrix_settings and bitrix_settings.enabled)

    async def create_for_user(
        self, user_id: int, payload: ServiceRequestCreate
    ) -> ServiceRequest:
        try:
            issue = ServiceIssueType(payload.issue_type)
        except ValueError:
            issue = ServiceIssueType.OTHER
        request = await self._repo.create(
            user_id=user_id,
            issue_type=issue,
            equipment=payload.equipment,
            description=payload.description,
            contact_phone=payload.contact_phone,
        )
        if self._bitrix_enabled:
            # Та же сессия → обращение и строка outbox коммитятся атомарно.
            user = await self._session.get(User, user_id)
            await self._outbox.create(
                source_type=BitrixLeadSource.SERVICE_REQUEST,
                source_id=request.id,
                payload=normalize_service_request(request, user),
            )
        log.info(
            "service_request_created",
            request_id=request.id,
            user_id=user_id,
            issue=issue.value,
        )
        return request

    async def list_for_user(self, user_id: int) -> Sequence[ServiceRequest]:
        return await self._repo.list_by_user(user_id)

    async def list_for_dealer(self, dealer_user_id: int) -> Sequence[ServiceRequest]:
        return await self._repo.list_for_dealer(dealer_user_id)

    async def get(self, request_id: int) -> ServiceRequest | None:
        return await self._repo.get_by_id(request_id)

    async def take(self, dealer_user_id: int, request_id: int) -> ServiceRequest | None:
        request = await self._repo.get_by_id(request_id)
        if request is None:
            return None
        if request.assigned_dealer_id not in (None, dealer_user_id):
            return None
        return await self._repo.assign_dealer(request, dealer_user_id)

    async def mark_done(
        self, dealer_user_id: int, request_id: int
    ) -> ServiceRequest | None:
        request = await self._repo.get_by_id(request_id)
        if request is None or request.assigned_dealer_id != dealer_user_id:
            return None
        return await self._repo.update_status(request, ServiceRequestStatus.DONE)

    async def mark_rejected(
        self, dealer_user_id: int, request_id: int
    ) -> ServiceRequest | None:
        request = await self._repo.get_by_id(request_id)
        if request is None or request.assigned_dealer_id != dealer_user_id:
            return None
        return await self._repo.update_status(request, ServiceRequestStatus.REJECTED)
