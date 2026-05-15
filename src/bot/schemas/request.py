from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bot.core.enums import RequestStatus


class ClientRequestCreate(BaseModel):
    contact_name: str = Field(min_length=2, max_length=256)
    contact_phone: str = Field(min_length=5, max_length=32)
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("contact_phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        if not cleaned:
            raise ValueError("phone must contain digits")
        return cleaned


class ClientRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    contact_name: str
    contact_phone: str
    comment: str | None
    status: RequestStatus
    assigned_dealer_id: int | None
    created_at: datetime
    updated_at: datetime
