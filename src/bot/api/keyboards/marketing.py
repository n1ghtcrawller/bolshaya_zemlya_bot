from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.core.enums import ContentType, SalesMaterialCategory, UserRole


class MktMenuCallback:
    DASHBOARD = "mkt:dashboard"
    USERS = "mkt:users"
    MATERIALS = "mkt:materials"
    BROADCASTS = "mkt:broadcasts"
    CONTENT = "mkt:content"
    EXPOS = "mkt:expos"
    EXPO_ASSISTANT = "mkt:expo:ai"
    CATALOG = "mkt:catalog"
    MODERATION = "mkt:mod"
    BACK_TO_MENU = "mkt:back_to_menu"


CB_CATALOG_NEW_CATEGORY = "mkt:cat:newcat"
CB_CATALOG_NEW_PRODUCT = "mkt:cat:newprod"
CB_CATALOG_PICK_CATEGORY = "mkt:cat:pick"

CB_MOD_VIEW = "mkt:mod:view"
CB_MOD_APPROVE = "mkt:mod:approve"
CB_MOD_REJECT = "mkt:mod:reject"

CB_DASH_SUMMARY = "mkt:dash:summary"
CB_DASH_DEALERS = "mkt:dash:dealers"
CB_DASH_PRODUCTS = "mkt:dash:products"

CB_USERS_ROLE = "mkt:users:role"
CB_USER_VIEW = "mkt:user:view"
CB_USER_SET_ROLE = "mkt:user:setrole"

CB_MATERIAL_CATEGORY = "mkt:mat:cat"

CB_BROADCAST_NEW = "mkt:bc:new"
CB_BROADCAST_LIST = "mkt:bc:list"
CB_BROADCAST_SEGMENT = "mkt:bc:seg"
CB_BROADCAST_CONFIRM = "mkt:bc:confirm"

CB_CONTENT_TYPE = "mkt:ct:type"
CB_CONTENT_NEW = "mkt:ct:new"
CB_CONTENT_VIEW = "mkt:ct:view"
CB_CONTENT_PENDING = "mkt:ct:pending"
CB_CONTENT_SUBMIT_CHOICE = "mkt:ct:sub"
CB_CONTENT_APPROVE = "mkt:ct:approve"
CB_CONTENT_REJECT = "mkt:ct:reject"
CB_CONTENT_PUBLISH = "mkt:ct:publish"
CB_CONTENT_ARCHIVE = "mkt:ct:archive"
CB_CONTENT_SUBMIT_NOW = "mkt:ct:submitnow"

CB_EXPO_NEW = "mkt:expo:new"
CB_EXPO_LIST = "mkt:expo:list"
CB_EXPO_VIEW = "mkt:expo:view"


def marketing_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Дашборд", callback_data=MktMenuCallback.DASHBOARD),
                InlineKeyboardButton(
                    text="👥 Пользователи", callback_data=MktMenuCallback.USERS
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📚 Материалы (загрузка)",
                    callback_data=MktMenuCallback.MATERIALS,
                ),
                InlineKeyboardButton(
                    text="📣 Рассылки", callback_data=MktMenuCallback.BROADCASTS
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Контент", callback_data=MktMenuCallback.CONTENT
                ),
                InlineKeyboardButton(
                    text="🎪 Выставки", callback_data=MktMenuCallback.EXPOS
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Каталог продукции",
                    callback_data=MktMenuCallback.CATALOG,
                ),
                InlineKeyboardButton(
                    text="🛡 Модерация материалов",
                    callback_data=MktMenuCallback.MODERATION,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤖 ИИ-помощник (Выставки)",
                    callback_data=MktMenuCallback.EXPO_ASSISTANT,
                ),
            ],
        ]
    )


def moderation_list_kb(material_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"Открыть #{mid}", callback_data=f"{CB_MOD_VIEW}:{mid}"
            )
        ]
        for mid in material_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def moderation_actions_kb(material_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"{CB_MOD_APPROVE}:{material_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"{CB_MOD_REJECT}:{material_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ К очереди", callback_data=MktMenuCallback.MODERATION
                )
            ],
        ]
    )


def catalog_admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Категория", callback_data=CB_CATALOG_NEW_CATEGORY
                ),
                InlineKeyboardButton(
                    text="➕ Товар", callback_data=CB_CATALOG_NEW_PRODUCT
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ],
        ]
    )


def catalog_pick_category_kb(categories: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=name, callback_data=f"{CB_CATALOG_PICK_CATEGORY}:{cid}"
            )
        ]
        for cid, name in categories
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dashboard_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Сводка", callback_data=CB_DASH_SUMMARY),
            ],
            [
                InlineKeyboardButton(text="📍 По диллерам", callback_data=CB_DASH_DEALERS),
                InlineKeyboardButton(text="📦 По продуктам", callback_data=CB_DASH_PRODUCTS),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ],
        ]
    )


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ]
        ]
    )


def roles_kb(callback_prefix: str, *, include_back: bool = True) -> InlineKeyboardMarkup:
    from bot.api.texts import ROLE_LABELS

    rows = [
        [
            InlineKeyboardButton(
                text=ROLE_LABELS[role.value], callback_data=f"{callback_prefix}:{role.value}"
            )
        ]
        for role in UserRole
    ]
    if include_back:
        rows.append(
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_card_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Сменить роль",
                    callback_data=f"{CB_USER_VIEW}:setrole:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ],
        ]
    )


def user_pick_role_kb(user_id: int) -> InlineKeyboardMarkup:
    from bot.api.texts import ROLE_LABELS

    rows = [
        [
            InlineKeyboardButton(
                text=ROLE_LABELS[role.value],
                callback_data=f"{CB_USER_SET_ROLE}:{user_id}:{role.value}",
            )
        ]
        for role in UserRole
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def users_list_kb(user_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"Открыть #{uid}", callback_data=f"{CB_USER_VIEW}:open:{uid}"
            )
        ]
        for uid in user_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def material_categories_kb() -> InlineKeyboardMarkup:
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
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def broadcasts_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Новая рассылка", callback_data=CB_BROADCAST_NEW
                ),
                InlineKeyboardButton(text="📜 История", callback_data=CB_BROADCAST_LIST),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ],
        ]
    )


def segment_kb() -> InlineKeyboardMarkup:
    from bot.api.texts import ROLE_LABELS

    rows = [
        [InlineKeyboardButton(text="Все пользователи", callback_data=f"{CB_BROADCAST_SEGMENT}:all")]
    ]
    for role in UserRole:
        rows.append(
            [
                InlineKeyboardButton(
                    text=ROLE_LABELS[role.value],
                    callback_data=f"{CB_BROADCAST_SEGMENT}:{role.value}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📣 Отправить", callback_data=f"{CB_BROADCAST_CONFIRM}:yes"
                ),
                InlineKeyboardButton(
                    text="✖️ Отмена", callback_data=f"{CB_BROADCAST_CONFIRM}:no"
                ),
            ]
        ]
    )


def content_types_kb(*, with_add: bool = True) -> InlineKeyboardMarkup:
    from bot.api.texts import CONTENT_TYPE_LABELS

    rows = [
        [
            InlineKeyboardButton(
                text=CONTENT_TYPE_LABELS[ct.value],
                callback_data=f"{CB_CONTENT_TYPE}:{ct.value}",
            )
        ]
        for ct in ContentType
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="🛡 На согласовании", callback_data=CB_CONTENT_PENDING
            )
        ]
    )
    if with_add:
        rows.append(
            [InlineKeyboardButton(text="➕ Добавить запись", callback_data=CB_CONTENT_NEW)]
        )
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_submit_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Черновик",
                    callback_data=f"{CB_CONTENT_SUBMIT_CHOICE}:draft",
                ),
                InlineKeyboardButton(
                    text="📤 На согласование",
                    callback_data=f"{CB_CONTENT_SUBMIT_CHOICE}:submit",
                ),
            ]
        ]
    )


def content_card_kb(item_id: int, status_value: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status_value == "draft":
        rows.append(
            [
                InlineKeyboardButton(
                    text="📤 На согласование",
                    callback_data=f"{CB_CONTENT_SUBMIT_NOW}:{item_id}",
                )
            ]
        )
    elif status_value == "pending_approval":
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"{CB_CONTENT_APPROVE}:{item_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"{CB_CONTENT_REJECT}:{item_id}",
                ),
            ]
        )
    elif status_value in {"approved", "scheduled"}:
        rows.append(
            [
                InlineKeyboardButton(
                    text="📢 Опубликовано",
                    callback_data=f"{CB_CONTENT_PUBLISH}:{item_id}",
                ),
                InlineKeyboardButton(
                    text="🗄 В архив",
                    callback_data=f"{CB_CONTENT_ARCHIVE}:{item_id}",
                ),
            ]
        )
    elif status_value == "rejected":
        rows.append(
            [
                InlineKeyboardButton(
                    text="📤 Повторно на согласование",
                    callback_data=f"{CB_CONTENT_SUBMIT_NOW}:{item_id}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_list_kb(item_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"Открыть #{i}", callback_data=f"{CB_CONTENT_VIEW}:{i}"
            )
        ]
        for i in item_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_new_type_kb() -> InlineKeyboardMarkup:
    """Выбор типа при создании новой записи (без кнопки 'добавить')."""
    from bot.api.texts import CONTENT_TYPE_LABELS

    rows = [
        [
            InlineKeyboardButton(
                text=CONTENT_TYPE_LABELS[ct.value],
                callback_data=f"{CB_CONTENT_NEW}:{ct.value}",
            )
        ]
        for ct in ContentType
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def expos_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Ближайшие", callback_data=CB_EXPO_LIST),
                InlineKeyboardButton(
                    text="➕ Добавить выставку", callback_data=CB_EXPO_NEW
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU
                )
            ],
        ]
    )


def expos_list_kb(expo_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Открыть #{eid}", callback_data=f"{CB_EXPO_VIEW}:{eid}")]
        for eid in expo_ids
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=MktMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
