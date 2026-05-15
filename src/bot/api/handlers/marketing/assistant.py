from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from httpx import AsyncClient

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import MktMenuCallback, back_to_menu
from bot.api.states.marketing import ExpoAssistantSG
from bot.api.texts import (
    MKT_EXPO_ASSISTANT_HEADER,
    MKT_EXPO_ASSISTANT_UNAVAILABLE,
    SALES_ASSISTANT_ANSWER_HEADER,
    SALES_ASSISTANT_THINKING,
)
from bot.config import Settings
from bot.core.exceptions import N8nUnavailableError
from bot.db.models.user import User
from bot.services.expo_assistant_service import ExpoAssistantService
from bot.services.n8n_client import N8nClient

assistant_router = Router(name="marketing.assistant")


@assistant_router.callback_query(F.data == MktMenuCallback.EXPO_ASSISTANT)
async def start_assistant(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(ExpoAssistantSG.waiting_question)
    await call.message.answer(MKT_EXPO_ASSISTANT_HEADER, reply_markup=cancel_kb())


@assistant_router.message(ExpoAssistantSG.waiting_question, F.text)
async def ask_assistant(
    message: Message,
    state: FSMContext,
    app_user: User,
    http_client: AsyncClient,
    settings: Settings,
) -> None:
    question = (message.text or "").strip()
    if not question:
        return
    thinking = await message.answer(SALES_ASSISTANT_THINKING)
    n8n = N8nClient(settings.n8n, http_client)
    service = ExpoAssistantService(n8n)
    try:
        answer = await service.ask(
            telegram_id=app_user.telegram_id,
            question=question,
            context={"user_id": app_user.id, "role": app_user.role.value},
        )
    except N8nUnavailableError:
        await thinking.delete()
        await message.answer(MKT_EXPO_ASSISTANT_UNAVAILABLE, reply_markup=back_to_menu())
        return

    await thinking.delete()
    await message.answer(f"{SALES_ASSISTANT_ANSWER_HEADER}\n\n{answer}")
    await message.answer(
        "Задайте следующий вопрос или вернитесь в меню.", reply_markup=back_to_menu()
    )
