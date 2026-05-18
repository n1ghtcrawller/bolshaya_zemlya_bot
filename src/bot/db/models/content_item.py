from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.enums import ContentStatus, ContentType, SalesMaterialFileType
from bot.db.base import Base, TimestampMixin


class ContentItem(Base, TimestampMixin):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(128))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    file_type: Mapped[SalesMaterialFileType | None] = mapped_column(
        Enum(SalesMaterialFileType, name="content_file_type", native_enum=False, length=32)
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(512))

    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", native_enum=False, length=32),
        nullable=False,
        default=ContentStatus.DRAFT,
        index=True,
    )
    approval_note: Mapped[str | None] = mapped_column(Text)
    approved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
