from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.client_request import ClientRequest
from bot.db.repositories.client_profile import ClientProfileRepository
from bot.db.repositories.client_request import ClientRequestRepository
from bot.logger import get_logger
from bot.schemas.request import ClientRequestCreate

log = get_logger(__name__)


class RequestService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._requests = ClientRequestRepository(session)
        self._profiles = ClientProfileRepository(session)

    async def create_for_user(self, user_id: int, payload: ClientRequestCreate) -> ClientRequest:
        request = await self._requests.create(
            user_id=user_id,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            comment=payload.comment,
            lead_type=payload.lead_type,
        )
        # Кэшируем телефон в профиле клиента — пригодится при следующих заявках.
        await self._profiles.upsert(user_id=user_id, phone=payload.contact_phone)
        log.info("client_request_created", request_id=request.id, user_id=user_id)
        return request

    async def list_for_user(self, user_id: int) -> Sequence[ClientRequest]:
        return await self._requests.list_by_user(user_id)

    async def get_for_user(self, user_id: int, request_id: int) -> ClientRequest | None:
        request = await self._requests.get_by_id(request_id)
        if request is None or request.user_id != user_id:
            return None
        return request
