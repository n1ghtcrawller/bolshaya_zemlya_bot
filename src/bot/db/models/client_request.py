from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import LeadType, RequestStatus
from bot.db.base import Base, TimestampMixin
from bot.db.models.user import User


class ClientRequest(Base, TimestampMixin):
    __tablename__ = "client_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    contact_name: Mapped[str] = mapped_column(String(256), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    lead_type: Mapped[LeadType] = mapped_column(
        Enum(LeadType, name="lead_type", native_enum=False, length=32),
        nullable=False,
        default=LeadType.REQUEST,
        index=True,
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status", native_enum=False, length=32),
        nullable=False,
        default=RequestStatus.NEW,
        index=True,
    )
    assigned_sales_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    assigned_dealer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id], lazy="joined")
