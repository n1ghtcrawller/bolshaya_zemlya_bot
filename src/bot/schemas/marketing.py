from pydantic import BaseModel

from bot.core.enums import RequestStatus, UserRole


class DashboardSnapshot(BaseModel):
    users_by_role: dict[UserRole, int]
    leads_by_status: dict[RequestStatus, int]
