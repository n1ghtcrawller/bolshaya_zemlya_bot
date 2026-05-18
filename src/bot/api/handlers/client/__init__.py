from aiogram import Router

from bot.api.filters import RoleFilter
from bot.api.handlers.client.callback import callback_router
from bot.api.handlers.client.catalog import catalog_router
from bot.api.handlers.client.chat_with_manager import chat_router
from bot.api.handlers.client.create_request import create_request_router
from bot.api.handlers.client.find_dealer import find_dealer_router
from bot.api.handlers.client.menu import client_menu_router
from bot.api.handlers.client.my_requests import my_requests_router
from bot.api.handlers.client.profile import profile_router
from bot.api.handlers.client.service import service_router
from bot.core.enums import UserRole


def build_client_router() -> Router:
    router = Router(name="client")
    client_only = RoleFilter(UserRole.CLIENT)
    router.message.filter(client_only)
    router.callback_query.filter(client_only)
    router.include_router(client_menu_router)
    router.include_router(catalog_router)
    router.include_router(profile_router)
    router.include_router(my_requests_router)
    router.include_router(create_request_router)
    router.include_router(chat_router)
    router.include_router(callback_router)
    router.include_router(service_router)
    router.include_router(find_dealer_router)
    return router


__all__ = ["build_client_router"]
