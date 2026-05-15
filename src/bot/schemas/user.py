from datetime import datetime

from pydantic import BaseModel, ConfigDict

from bot.core.enums import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    full_name: str
    role: UserRole
    is_active: bool
    language_code: str | None
    created_at: datetime
    updated_at: datetime


class TelegramUserData(BaseModel):
    """Подмножество данных из aiogram.types.User для создания/обновления записи."""

    telegram_id: int
    username: str | None = None
    full_name: str
    language_code: str | None = None
