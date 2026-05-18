from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.enums import BroadcastStatus, SalesMaterialFileType, UserRole
from bot.db.base import Base, TimestampMixin, lower_enum


class Broadcast(Base, TimestampMixin):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    text: Mapped[str | None] = mapped_column(Text)
    file_type: Mapped[SalesMaterialFileType | None] = mapped_column(
        lower_enum(SalesMaterialFileType, name="broadcast_file_type")
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(512))

    target_role: Mapped[UserRole | None] = mapped_column(
        lower_enum(UserRole, name="broadcast_target_role"),
        index=True,
    )

    status: Mapped[BroadcastStatus] = mapped_column(
        lower_enum(BroadcastStatus, name="broadcast_status"),
        nullable=False,
        default=BroadcastStatus.DRAFT,
        index=True,
    )
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
