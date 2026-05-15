from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.enums import BroadcastStatus, SalesMaterialFileType, UserRole
from bot.db.base import Base, TimestampMixin


class Broadcast(Base, TimestampMixin):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    text: Mapped[str | None] = mapped_column(Text)
    file_type: Mapped[SalesMaterialFileType | None] = mapped_column(
        Enum(SalesMaterialFileType, name="broadcast_file_type", native_enum=False, length=32)
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(512))

    target_role: Mapped[UserRole | None] = mapped_column(
        Enum(UserRole, name="broadcast_target_role", native_enum=False, length=32),
        index=True,
    )

    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, name="broadcast_status", native_enum=False, length=32),
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
