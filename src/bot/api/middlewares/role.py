from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineQuery,
    Message,
    TelegramObject,
    Update,
    User as TgUser,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.cache.role_cache import RoleCache
from bot.schemas.user import TelegramUserData
from bot.services.user_service import UserService


def _tg_user(event: TelegramObject) -> TgUser | None:
    # Outer middleware на dp.update получает Update — вытаскиваем from_user
    # из вложенного события. Поддерживаем и прямые Message/CallbackQuery
    # на случай повторного использования middleware в других местах.
    if isinstance(event, Update):
        for candidate in (
            event.message,
            event.edited_message,
            event.channel_post,
            event.edited_channel_post,
            event.callback_query,
            event.inline_query,
            event.chosen_inline_result,
            event.shipping_query,
            event.pre_checkout_query,
            event.poll_answer,
            event.my_chat_member,
            event.chat_member,
            event.chat_join_request,
        ):
            if candidate is not None and getattr(candidate, "from_user", None) is not None:
                return candidate.from_user
        return None
    if isinstance(event, (Message, CallbackQuery, InlineQuery, ChatMemberUpdated)):
        return event.from_user
    return None


def _full_name(user: TgUser) -> str:
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    return name or (user.username or f"user_{user.id}")


class RoleMiddleware(BaseMiddleware):
    """Определяет роль пользователя.

    - сначала пытается достать из Redis-кэша;
    - если нет — идёт в БД через UserService;
    - если пользователя в БД нет — создаёт как CLIENT (auto-onboarding).

    Кладёт в data: ``app_user`` (модель User) и ``role``.
    """

    def __init__(self, role_cache: RoleCache) -> None:
        super().__init__()
        self._role_cache = role_cache

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = _tg_user(event)
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        service = UserService(session, self._role_cache)
        user, _ = await service.get_or_create(
            TelegramUserData(
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=_full_name(tg_user),
                language_code=tg_user.language_code,
            )
        )
        data["app_user"] = user
        data["role"] = user.role
        data["user_service"] = service
        return await handler(event, data)
