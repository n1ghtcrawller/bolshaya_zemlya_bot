from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


class ClientMenuCallback:
    CATALOG = "client:catalog"
    PICKER = "client:picker"
    NEW_REQUEST = "client:new_request"
    FIND_DEALER = "client:find_dealer"
    SERVICE = "client:service"
    CHAT = "client:chat"
    CALL = "client:call"
    MY_REQUESTS = "client:my_requests"
    PROFILE = "client:profile"


def client_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📚 Каталог", callback_data=ClientMenuCallback.CATALOG),
                InlineKeyboardButton(
                    text="🔍 Подобрать технику", callback_data=ClientMenuCallback.PICKER
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Оставить заявку", callback_data=ClientMenuCallback.NEW_REQUEST
                ),
                InlineKeyboardButton(
                    text="📍 Найти диллера", callback_data=ClientMenuCallback.FIND_DEALER
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔧 Сервис и запчасти", callback_data=ClientMenuCallback.SERVICE
                ),
                InlineKeyboardButton(
                    text="💬 Чат с менеджером", callback_data=ClientMenuCallback.CHAT
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📞 Заказать звонок", callback_data=ClientMenuCallback.CALL
                ),
                InlineKeyboardButton(
                    text="📋 Мои заявки", callback_data=ClientMenuCallback.MY_REQUESTS
                ),
            ],
            [
                InlineKeyboardButton(text="👤 Профиль", callback_data=ClientMenuCallback.PROFILE),
            ],
        ]
    )


def back_to_menu(callback_data: str = "client:back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data=callback_data)]]
    )


def share_contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
            [KeyboardButton(text="✖️ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✖️ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_request_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="client:req:confirm"),
                InlineKeyboardButton(text="✖️ Отмена", callback_data="client:req:cancel"),
            ]
        ]
    )


def requests_list_kb(request_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Заявка #{rid}", callback_data=f"client:req:view:{rid}")]
        for rid in request_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data="client:back_to_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


CB_FIND_REGION = "client:dir:region"
CB_FIND_DEALER = "client:dir:dealer"
CB_DEALER_REQUEST = "client:dir:dealer:request"
CB_DEALER_CALLBACK = "client:dir:dealer:callback"


def find_dealer_regions_kb(region_tokens: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """region_tokens — список (название, token) ровно как в `regions_kb` у Sales."""
    rows = [
        [
            InlineKeyboardButton(text=name, callback_data=f"{CB_FIND_REGION}:{token}")
        ]
        for name, token in region_tokens
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data="client:back_to_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def find_dealer_list_kb(dealers: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=name, callback_data=f"{CB_FIND_DEALER}:{dealer_id}"
            )
        ]
        for dealer_id, name in dealers
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data="client:back_to_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def find_dealer_card_kb(*, dealer_id: int, tg_url: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if tg_url is not None:
        rows.append([InlineKeyboardButton(text="💬 Написать в TG", url=tg_url)])
    rows.append(
        [
            InlineKeyboardButton(
                text="📝 Оставить заявку",
                callback_data=f"{CB_DEALER_REQUEST}:{dealer_id}",
            ),
            InlineKeyboardButton(
                text="📞 Заказать звонок",
                callback_data=f"{CB_DEALER_CALLBACK}:{dealer_id}",
            ),
        ]
    )
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data="client:back_to_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_issue_types_kb() -> InlineKeyboardMarkup:
    from bot.api.texts import SERVICE_ISSUE_LABELS

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=SERVICE_ISSUE_LABELS["warranty"],
                    callback_data="client:srv:issue:warranty",
                ),
                InlineKeyboardButton(
                    text=SERVICE_ISSUE_LABELS["repair"],
                    callback_data="client:srv:issue:repair",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=SERVICE_ISSUE_LABELS["spare_parts"],
                    callback_data="client:srv:issue:spare_parts",
                ),
                InlineKeyboardButton(
                    text=SERVICE_ISSUE_LABELS["other"],
                    callback_data="client:srv:issue:other",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data="client:back_to_menu"
                )
            ],
        ]
    )
