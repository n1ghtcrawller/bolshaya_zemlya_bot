from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import BroadcastStatus, SalesMaterialFileType, UserRole
from bot.db.models.broadcast import Broadcast


class BroadcastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, broadcast_id: int) -> Broadcast | None:
        return await self._session.get(Broadcast, broadcast_id)

    async def list_recent(self, *, limit: int = 20) -> Sequence[Broadcast]:
        stmt = select(Broadcast).order_by(Broadcast.created_at.desc()).limit(limit)
        return (await self._session.scalars(stmt)).all()

    async def create(
        self,
        *,
        text: str | None,
        file_type: SalesMaterialFileType | None,
        telegram_file_id: str | None,
        target_role: UserRole | None,
        created_by_user_id: int | None,
        status: BroadcastStatus = BroadcastStatus.DRAFT,
    ) -> Broadcast:
        broadcast = Broadcast(
            text=text,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            target_role=target_role,
            created_by_user_id=created_by_user_id,
            status=status,
        )
        self._session.add(broadcast)
        await self._session.flush()
        return broadcast

    async def mark_sent(
        self,
        broadcast: Broadcast,
        *,
        sent_count: int,
        sent_at: datetime,
    ) -> Broadcast:
        broadcast.status = BroadcastStatus.SENT
        broadcast.sent_count = sent_count
        broadcast.sent_at = sent_at
        broadcast.error = None
        await self._session.flush()
        return broadcast

    async def mark_failed(self, broadcast: Broadcast, error: str) -> Broadcast:
        broadcast.status = BroadcastStatus.FAILED
        broadcast.error = error
        await self._session.flush()
        return broadcast

    async def mark_queued(self, broadcast: Broadcast) -> Broadcast:
        broadcast.status = BroadcastStatus.QUEUED
        await self._session.flush()
        return broadcast
