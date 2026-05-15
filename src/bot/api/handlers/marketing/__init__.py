from aiogram import Router

from bot.api.filters import RoleFilter
from bot.api.handlers.marketing.assistant import assistant_router
from bot.api.handlers.marketing.broadcasts import broadcasts_router
from bot.api.handlers.marketing.catalog_admin import catalog_admin_router
from bot.api.handlers.marketing.content import content_router
from bot.api.handlers.marketing.dashboard import dashboard_router
from bot.api.handlers.marketing.expos import expos_router
from bot.api.handlers.marketing.materials_upload import materials_router
from bot.api.handlers.marketing.menu import menu_router
from bot.api.handlers.marketing.users import users_router
from bot.core.enums import UserRole


def build_marketing_router() -> Router:
    router = Router(name="marketing")
    mkt_only = RoleFilter(UserRole.MARKETING)
    router.message.filter(mkt_only)
    router.callback_query.filter(mkt_only)
    router.include_router(menu_router)
    router.include_router(dashboard_router)
    router.include_router(users_router)
    router.include_router(materials_router)
    router.include_router(broadcasts_router)
    router.include_router(content_router)
    router.include_router(expos_router)
    router.include_router(catalog_admin_router)
    router.include_router(assistant_router)
    return router


__all__ = ["build_marketing_router"]
