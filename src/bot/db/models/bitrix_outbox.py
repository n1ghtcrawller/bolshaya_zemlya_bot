from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.enums import BitrixLeadSource, BitrixSyncStatus
from bot.db.base import Base, TimestampMixin, lower_enum


class BitrixOutbox(Base, TimestampMixin):
    """Очередь гарантированной доставки лидов в Bitrix24.

    Строка создаётся в той же транзакции, что и сам лид (client_request /
    service_request). Фоновый воркер (bitrix_dispatcher) досылает в Bitrix
    с ретраями и backoff до успеха либо до max_attempts.
    """

    __tablename__ = "bitrix_outbox"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_type: Mapped[BitrixLeadSource] = mapped_column(
        lower_enum(BitrixLeadSource, name="bitrix_lead_source"), nullable=False
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Нормализованные данные лида (lead_type/name/phone/comment/...) — поля Bitrix
    # собираются из payload при отправке (см. bitrix_lead_builder.build_lead_fields).
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[BitrixSyncStatus] = mapped_column(
        lower_enum(BitrixSyncStatus, name="bitrix_sync_status"),
        nullable=False,
        default=BitrixSyncStatus.PENDING,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    bitrix_lead_id: Mapped[int | None] = mapped_column(Integer)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
