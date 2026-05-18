from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import ApprovalStatus
from bot.db.base import Base, TimestampMixin
from bot.db.models.client_request import ClientRequest


class LeadApproval(Base, TimestampMixin):
    """Запрос на согласование передачи лида от Sales к Дилеру (эскалация HeadOfSales).

    Жизненный цикл:
      pending → approved (head_of_sales одобрил) → лид передаётся диллеру
      pending → rejected (head_of_sales отклонил) → лид остаётся у sales
    """

    __tablename__ = "lead_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("client_requests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sales_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    proposed_dealer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="lead_approval_status", native_enum=False, length=32),
        nullable=False,
        default=ApprovalStatus.PENDING,
        index=True,
    )
    decision_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)

    lead: Mapped[ClientRequest] = relationship(lazy="joined")
