from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.core.enums import RequestStatus, SalesMaterialCategory


class DealerMenuCallback:
    LEADS = "dealer:leads"
    MATERIALS = "dealer:materials"
    SERVICE_REQUESTS = "dealer:service"
    STATS = "dealer:stats"
    PROFILE = "dealer:profile"
    BACK_TO_MENU = "dealer:back_to_menu"


CB_LEAD_VIEW = "dealer:lead:view"
CB_LEAD_TAKE = "dealer:lead:take"
CB_LEAD_DONE = "dealer:lead:done"
CB_LEAD_REJECT = "dealer:lead:reject"

CB_MATERIAL_CATEGORY = "dealer:mat:cat"
CB_MATERIAL_PAGE = "dealer:mat:page"
CB_MATERIAL_SEND = "dealer:mat:send"

CB_PROFILE_EDIT = "dealer:profile:edit"

CB_SERVICE_VIEW = "dealer:srv:view"
CB_SERVICE_TAKE = "dealer:srv:take"
CB_SERVICE_DONE = "dealer:srv:done"
CB_SERVICE_REJECT = "dealer:srv:reject"

CB_MATERIAL_SUBMIT = "dealer:mat:submit"
CB_MATERIAL_SUBMIT_CATEGORY = "dealer:mat:submit:cat"


def dealer_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Новые лиды", callback_data=DealerMenuCallback.LEADS
                ),
                InlineKeyboardButton(
                    text="📚 Продающие материалы",
                    callback_data=DealerMenuCallback.MATERIALS,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔧 Сервисные обращения",
                    callback_data=DealerMenuCallback.SERVICE_REQUESTS,
                ),
                InlineKeyboardButton(
                    text="📊 Статистика", callback_data=DealerMenuCallback.STATS
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👤 Профиль", callback_data=DealerMenuCallback.PROFILE
                ),
            ],
        ]
    )


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU
                )
            ]
        ]
    )


def leads_list_kb(lead_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Открыть #{lid}", callback_data=f"{CB_LEAD_VIEW}:{lid}")]
        for lid in lead_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lead_actions_kb(lead_id: int, status: RequestStatus) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == RequestStatus.TRANSFERRED_TO_DEALER:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Взять в работу",
                    callback_data=f"{CB_LEAD_TAKE}:{lead_id}",
                )
            ]
        )
    if status in (RequestStatus.TRANSFERRED_TO_DEALER, RequestStatus.IN_PROGRESS):
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Выполнено", callback_data=f"{CB_LEAD_DONE}:{lead_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"{CB_LEAD_REJECT}:{lead_id}"
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ К списку лидов", callback_data=DealerMenuCallback.LEADS
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def materials_categories_kb() -> InlineKeyboardMarkup:
    from bot.api.texts import MATERIAL_CATEGORY_LABELS

    rows = [
        [
            InlineKeyboardButton(
                text=MATERIAL_CATEGORY_LABELS[cat.value],
                callback_data=f"{CB_MATERIAL_CATEGORY}:{cat.value}",
            )
        ]
        for cat in SalesMaterialCategory
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def materials_page_kb(
    category: SalesMaterialCategory,
    page: int,
    pages: int,
    material_ids: list[int],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for mid in material_ids:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📎 Скачать #{mid}",
                    callback_data=f"{CB_MATERIAL_SEND}:{mid}",
                )
            ]
        )
    if pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"{CB_MATERIAL_PAGE}:{category.value}:{page - 1}",
                )
            )
        nav.append(
            InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="dealer:noop")
        )
        if page < pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"{CB_MATERIAL_PAGE}:{category.value}:{page + 1}",
                )
            )
        rows.append(nav)
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ К разделам", callback_data=DealerMenuCallback.MATERIALS
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_list_kb(request_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Открыть #{rid}", callback_data=f"{CB_SERVICE_VIEW}:{rid}")]
        for rid in request_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_actions_kb(request_id: int, status_value: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status_value == "new":
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Взять в работу", callback_data=f"{CB_SERVICE_TAKE}:{request_id}"
                )
            ]
        )
    if status_value in ("new", "in_progress"):
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Закрыть", callback_data=f"{CB_SERVICE_DONE}:{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"{CB_SERVICE_REJECT}:{request_id}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ К списку",
                callback_data=DealerMenuCallback.SERVICE_REQUESTS,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def material_submit_categories_kb() -> InlineKeyboardMarkup:
    from bot.api.texts import MATERIAL_CATEGORY_LABELS
    from bot.core.enums import SalesMaterialCategory

    rows = [
        [
            InlineKeyboardButton(
                text=MATERIAL_CATEGORY_LABELS[cat.value],
                callback_data=f"{CB_MATERIAL_SUBMIT_CATEGORY}:{cat.value}",
            )
        ]
        for cat in SalesMaterialCategory
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def materials_categories_with_submit_kb() -> InlineKeyboardMarkup:
    """Категории материалов + кнопка «загрузить локальный»."""
    from bot.api.texts import MATERIAL_CATEGORY_LABELS
    from bot.core.enums import SalesMaterialCategory

    rows = [
        [
            InlineKeyboardButton(
                text=MATERIAL_CATEGORY_LABELS[cat.value],
                callback_data=f"{CB_MATERIAL_CATEGORY}:{cat.value}",
            )
        ]
        for cat in SalesMaterialCategory
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="✍️ Загрузить на согласование",
                callback_data=CB_MATERIAL_SUBMIT,
            )
        ]
    )
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Телефон", callback_data=f"{CB_PROFILE_EDIT}:phone"
                ),
                InlineKeyboardButton(
                    text="✏️ Компания", callback_data=f"{CB_PROFILE_EDIT}:company"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Регион", callback_data=f"{CB_PROFILE_EDIT}:region"
                ),
                InlineKeyboardButton(
                    text="✏️ Адрес", callback_data=f"{CB_PROFILE_EDIT}:address"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ О компании",
                    callback_data=f"{CB_PROFILE_EDIT}:description",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=DealerMenuCallback.BACK_TO_MENU
                )
            ],
        ]
    )
