from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.dealer import DealerMenuCallback, back_to_menu
from bot.api.texts import DEALER_STATS_TEMPLATE
from bot.db.models.user import User
from bot.services.dealer_lead_service import DealerLeadService

stats_router = Router(name="dealer.stats")


@stats_router.callback_query(F.data == DealerMenuCallback.STATS)
async def show_stats(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    service = DealerLeadService(session)
    stats = await service.stats(app_user.id)
    await call.message.answer(
        DEALER_STATS_TEMPLATE.format(
            total=stats.total,
            new=stats.new,
            in_progress=stats.in_progress,
            done=stats.done,
            rejected=stats.rejected,
        ),
        reply_markup=back_to_menu(),
    )
