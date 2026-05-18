from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.enums import ApprovalStatus, SalesMaterialCategory, SalesMaterialFileType
from bot.db.base import Base, TimestampMixin, lower_enum


class SalesMaterial(Base, TimestampMixin):
    __tablename__ = "sales_materials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    category: Mapped[SalesMaterialCategory] = mapped_column(
        lower_enum(SalesMaterialCategory, name="sales_material_category"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    file_type: Mapped[SalesMaterialFileType] = mapped_column(
        lower_enum(SalesMaterialFileType, name="sales_material_file_type"),
        nullable=False,
    )
    telegram_file_id: Mapped[str] = mapped_column(String(512), nullable=False)

    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    approval_status: Mapped[ApprovalStatus] = mapped_column(
        lower_enum(ApprovalStatus, name="material_approval_status"),
        nullable=False,
        default=ApprovalStatus.APPROVED,
        index=True,
    )
    approval_note: Mapped[str | None] = mapped_column(Text)
    approved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
