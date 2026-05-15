from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base, TimestampMixin
from bot.db.models.product_category import ProductCategory


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("product_categories.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(512))
    full_description: Mapped[str | None] = mapped_column(Text)
    price_text: Mapped[str | None] = mapped_column(String(128))
    specs: Mapped[str | None] = mapped_column(Text)
    main_photo_file_id: Mapped[str | None] = mapped_column(String(512))

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    category: Mapped[ProductCategory] = relationship(lazy="joined")
