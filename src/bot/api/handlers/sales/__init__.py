from aiogram import Router

from bot.api.filters import RoleFilter
from bot.api.handlers.sales.assistant import assistant_router
from bot.api.handlers.sales.find_dealer import find_dealer_router
from bot.api.handlers.sales.leads import leads_router
from bot.api.handlers.sales.menu import menu_router
from bot.core.enums import UserRole


def build_sales_router() -> Router:
    router = Router(name="sales")
    sales_only = RoleFilter(UserRole.SALES)
    router.message.filter(sales_only)
    router.callback_query.filter(sales_only)
    router.include_router(menu_router)
    router.include_router(leads_router)
    router.include_router(find_dealer_router)
    router.include_router(assistant_router)
    return router


__all__ = ["build_sales_router"]
