from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import LeadType, RequestStatus
from bot.db.base import Base, TimestampMixin, lower_enum
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
        lower_enum(LeadType, name="lead_type"),
        nullable=False,
        default=LeadType.REQUEST,
        index=True,
    )
    status: Mapped[RequestStatus] = mapped_column(
        lower_enum(RequestStatus, name="request_status"),
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
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), index=True
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id], lazy="joined")
