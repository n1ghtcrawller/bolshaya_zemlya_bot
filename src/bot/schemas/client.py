from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    phone: str | None
    region: str | None
    company: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime


class ClientProfileUpdate(BaseModel):
    phone: str | None = None
    region: str | None = None
    company: str | None = None
    email: str | None = None
