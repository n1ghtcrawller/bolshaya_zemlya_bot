from aiogram import Router

from bot.api.handlers.client import build_client_router
from bot.api.handlers.common import common_router
from bot.api.handlers.dealer import build_dealer_router
from bot.api.handlers.marketing import build_marketing_router
from bot.api.handlers.sales import build_sales_router
from bot.api.handlers.start import start_router


def build_root_router() -> Router:
    router = Router(name="root")
    router.include_router(start_router)
    router.include_router(build_client_router())
    router.include_router(build_dealer_router())
    router.include_router(build_sales_router())
    router.include_router(build_marketing_router())
    router.include_router(common_router)
    return router


__all__ = ["build_root_router"]
