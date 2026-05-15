from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base, TimestampMixin
from bot.db.models.user import User


class ClientProfile(Base, TimestampMixin):
    __tablename__ = "client_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    phone: Mapped[str | None] = mapped_column(String(32))
    region: Mapped[str | None] = mapped_column(String(128))
    company: Mapped[str | None] = mapped_column(String(256))
    email: Mapped[str | None] = mapped_column(String(128))

    user: Mapped[User] = relationship(lazy="joined")
