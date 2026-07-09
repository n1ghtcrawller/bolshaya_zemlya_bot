from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import BitrixLeadSource, BitrixSyncStatus
from bot.db.models.bitrix_outbox import BitrixOutbox


class BitrixOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_type: BitrixLeadSource,
        source_id: int,
        payload: dict,
    ) -> BitrixOutbox:
        row = BitrixOutbox(
            source_type=source_type,
            source_id=source_id,
            payload=payload,
            status=BitrixSyncStatus.PENDING,
            attempts=0,
            next_attempt_at=datetime.now(tz=timezone.utc),  # доступно к отправке сразу
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_due(
        self, now: datetime, *, limit: int = 20
    ) -> Sequence[BitrixOutbox]:
        stmt = (
            select(BitrixOutbox)
            .where(
                BitrixOutbox.status == BitrixSyncStatus.PENDING,
                BitrixOutbox.next_attempt_at <= now,
            )
            .order_by(BitrixOutbox.next_attempt_at.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()
