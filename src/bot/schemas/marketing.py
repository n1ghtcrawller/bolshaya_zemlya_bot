from pydantic import BaseModel

from bot.core.enums import RequestStatus, UserRole


class DashboardSnapshot(BaseModel):
    users_by_role: dict[UserRole, int]
    leads_by_status: dict[RequestStatus, int]


class DealerBreakdownRow(BaseModel):
    dealer_id: int
    full_name: str
    company: str | None
    total: int
    in_progress: int
    done: int
    rejected: int
    transferred: int


class ProductTopRow(BaseModel):
    product_id: int
    name: str
    category: str
    requests_total: int
