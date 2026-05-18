"""Политика согласований по ролям.

Если в БД есть назначенный head — одобрять может только он. Если нет — fallback
на любого пользователя с базовой ролью, чтобы система не зависала.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import UserRole
from bot.db.models.user import User
from bot.db.repositories.user import UserRepository


async def can_approve_marketing(session: AsyncSession, user: User) -> bool:
    if user.role is UserRole.HEAD_OF_MARKETING:
        return True
    if user.role is not UserRole.MARKETING:
        return False
    # fallback: если head_of_marketing нет в БД — обычный маркетолог может одобрять
    return not await UserRepository(session).has_role(UserRole.HEAD_OF_MARKETING)
