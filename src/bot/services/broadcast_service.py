from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import SalesMaterialFileType, UserRole
from bot.core.exceptions import N8nUnavailableError
from bot.db.models.broadcast import Broadcast
from bot.db.repositories.broadcast import BroadcastRepository
from bot.db.repositories.user import UserRepository
from bot.logger import get_logger
from bot.services.n8n_client import N8nClient

log = get_logger(__name__)


class BroadcastService:
    """Маркетинговые рассылки. Отправка делегируется n8n.

    Workflow в n8n принимает payload и сам рассылает через Telegram Bot API,
    избегая блокировки бота на тысячах sendMessage.
    """

    def __init__(self, session: AsyncSession, n8n: N8nClient) -> None:
        self._session = session
        self._broadcasts = BroadcastRepository(session)
        self._users = UserRepository(session)
        self._n8n = n8n

    async def list_recent(self) -> Sequence[Broadcast]:
        return await self._broadcasts.list_recent()

    async def create_draft(
        self,
        *,
        text: str | None,
        file_type: SalesMaterialFileType | None,
        telegram_file_id: str | None,
        target_role: UserRole | None,
        created_by_user_id: int | None,
    ) -> Broadcast:
        return await self._broadcasts.create(
            text=text,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            target_role=target_role,
            created_by_user_id=created_by_user_id,
        )

    async def send(self, broadcast: Broadcast) -> Broadcast:
        recipients = await self._users.list_telegram_ids_by_role(broadcast.target_role)
        if not recipients:
            await self._broadcasts.mark_failed(broadcast, "no_recipients")
            return broadcast

        await self._broadcasts.mark_queued(broadcast)
        payload = {
            "broadcast_id": broadcast.id,
            "text": broadcast.text,
            "file_type": broadcast.file_type.value if broadcast.file_type else None,
            "telegram_file_id": broadcast.telegram_file_id,
            "target_role": broadcast.target_role.value if broadcast.target_role else None,
            "recipients": list(recipients),
        }
        try:
            await self._n8n.broadcast(payload)
        except N8nUnavailableError as exc:
            await self._broadcasts.mark_failed(broadcast, str(exc))
            log.warning("broadcast_send_failed", broadcast_id=broadcast.id, error=str(exc))
            raise

        broadcast = await self._broadcasts.mark_sent(
            broadcast,
            sent_count=len(recipients),
            sent_at=datetime.now(tz=timezone.utc),
        )
        log.info(
            "broadcast_sent", broadcast_id=broadcast.id, sent_count=len(recipients)
        )
        return broadcast
