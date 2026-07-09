"""Фоновый воркер доставки лидов в Bitrix24 из очереди bitrix_outbox.

Запускается AsyncIOScheduler-ом раз в `BITRIX_DISPATCH_INTERVAL_SECONDS` секунд.
Берёт строки в статусе pending со сроком next_attempt_at <= now, шлёт в Bitrix
crm.lead.add. При ошибке наращивает attempts и сдвигает next_attempt_at
(экспоненциальный backoff); после max_attempts помечает строку failed.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import BitrixSettings
from bot.core.enums import BitrixSyncStatus
from bot.core.exceptions import BitrixUnavailableError
from bot.db.models.bitrix_outbox import BitrixOutbox
from bot.db.repositories.bitrix_outbox import BitrixOutboxRepository
from bot.logger import get_logger
from bot.services.bitrix_client import BitrixClient
from bot.services.bitrix_lead_builder import build_lead_fields

log = get_logger(__name__)

_MAX_BACKOFF_SECONDS = 3600


def _next_attempt_delay(attempts: int, settings: BitrixSettings) -> int:
    base = settings.retry_backoff_base_seconds
    return min(base * (2 ** (attempts - 1)), _MAX_BACKOFF_SECONDS)


def _pick_assignee(row: BitrixOutbox, settings: BitrixSettings) -> int | None:
    """Round-robin по ID ответственных. Стабилен для одной строки (по row.id),
    поэтому ретраи идут тому же менеджеру."""
    ids = settings.responsible_ids()
    if not ids:
        return None
    return ids[(row.id or 0) % len(ids)]


async def _send_one(
    row: BitrixOutbox,
    bitrix: BitrixClient,
    settings: BitrixSettings,
    now: datetime,
) -> bool:
    fields = build_lead_fields(row.payload, settings, _pick_assignee(row, settings))
    try:
        lead_id = await bitrix.create_lead(fields)
    except BitrixUnavailableError as exc:
        row.attempts += 1
        row.last_error = str(exc)[:2000]
        if row.attempts >= settings.max_attempts:
            row.status = BitrixSyncStatus.FAILED
            log.warning(
                "bitrix_lead_failed",
                outbox_id=row.id,
                attempts=row.attempts,
                error=row.last_error,
            )
        else:
            delay = _next_attempt_delay(row.attempts, settings)
            row.next_attempt_at = now + timedelta(seconds=delay)
            log.info(
                "bitrix_lead_retry",
                outbox_id=row.id,
                attempts=row.attempts,
                retry_in=delay,
            )
        return False

    row.status = BitrixSyncStatus.SENT
    row.bitrix_lead_id = lead_id
    row.last_error = None
    log.info("bitrix_lead_sent", outbox_id=row.id, bitrix_lead_id=lead_id)
    return True


async def dispatch_pending_leads(
    sessionmaker: async_sessionmaker[AsyncSession],
    bitrix: BitrixClient,
    settings: BitrixSettings,
) -> int:
    """Один цикл доставки. Возвращает количество успешно отправленных лидов."""
    now = datetime.now(tz=timezone.utc)
    sent = 0
    async with sessionmaker() as session:
        repo = BitrixOutboxRepository(session)
        rows = await repo.list_due(now)
        if not rows:
            return 0
        log.info("bitrix_dispatcher_tick", candidates=len(rows))
        for row in rows:
            if await _send_one(row, bitrix, settings, now):
                sent += 1
        await session.commit()
    return sent
