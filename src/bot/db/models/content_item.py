from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.enums import ContentStatus, ContentType, SalesMaterialFileType
from bot.db.base import Base, TimestampMixin, lower_enum


class ContentItem(Base, TimestampMixin):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    type: Mapped[ContentType] = mapped_column(
        lower_enum(ContentType, name="content_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(128))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    file_type: Mapped[SalesMaterialFileType | None] = mapped_column(
        lower_enum(SalesMaterialFileType, name="content_file_type")
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(512))

    status: Mapped[ContentStatus] = mapped_column(
        lower_enum(ContentStatus, name="content_status"),
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
