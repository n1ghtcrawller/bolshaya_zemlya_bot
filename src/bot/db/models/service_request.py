from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import ServiceIssueType, ServiceRequestStatus
from bot.db.base import Base, TimestampMixin
from bot.db.models.user import User


class ServiceRequest(Base, TimestampMixin):
    """Сервисное обращение клиента — отдельная ветка (гарантия / ремонт / запчасти).

    Не путать с ClientRequest (лидом). Создаётся Клиентом, обслуживается Дилером.
    """

    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    issue_type: Mapped[ServiceIssueType] = mapped_column(
        Enum(ServiceIssueType, name="service_issue_type", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    equipment: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)

    status: Mapped[ServiceRequestStatus] = mapped_column(
        Enum(ServiceRequestStatus, name="service_request_status", native_enum=False, length=32),
        nullable=False,
        default=ServiceRequestStatus.NEW,
        index=True,
    )
    assigned_dealer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id], lazy="joined")
