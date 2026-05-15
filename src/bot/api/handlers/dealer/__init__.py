from aiogram import Router

from bot.api.filters import RoleFilter
from bot.api.handlers.dealer.leads import leads_router
from bot.api.handlers.dealer.materials import materials_router
from bot.api.handlers.dealer.menu import menu_router
from bot.api.handlers.dealer.profile import profile_router
from bot.api.handlers.dealer.service_requests import service_requests_router
from bot.api.handlers.dealer.stats import stats_router
from bot.core.enums import UserRole


def build_dealer_router() -> Router:
    router = Router(name="dealer")
    dealer_only = RoleFilter(UserRole.DEALER)
    router.message.filter(dealer_only)
    router.callback_query.filter(dealer_only)
    router.include_router(menu_router)
    router.include_router(leads_router)
    router.include_router(materials_router)
    router.include_router(service_requests_router)
    router.include_router(stats_router)
    router.include_router(profile_router)
    return router


__all__ = ["build_dealer_router"]
