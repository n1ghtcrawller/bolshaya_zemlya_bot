from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from bot.core.enums import UserRole


class RoleFilter(BaseFilter):
    """Пропускает апдейт, только если data['role'] входит в список разрешённых ролей."""

    def __init__(self, *roles: UserRole) -> None:
        self.roles = set(roles)

    async def __call__(self, event: TelegramObject, role: UserRole | None = None) -> bool:
        return role in self.roles
