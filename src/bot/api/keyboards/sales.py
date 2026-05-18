import hashlib

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.core.enums import RequestStatus


class SalesMenuCallback:
    LEADS_NEW = "sales:leads:new"
    LEADS_IN_PROGRESS = "sales:leads:in_progress"
    LEADS_TRANSFERRED = "sales:leads:transferred"
    FIND_DEALER = "sales:dealer:find"
    ASSISTANT = "sales:ai"
    HOS_QUEUE = "sales:hos:queue"
    BACK_TO_MENU = "sales:back_to_menu"


CB_HOS_VIEW = "sales:hos:view"
CB_HOS_APPROVE = "sales:hos:approve"
CB_HOS_REJECT = "sales:hos:reject"


CB_LEAD_VIEW = "sales:lead:view"
CB_LEAD_TAKE = "sales:lead:take"
CB_LEAD_TRANSFER_REGION = "sales:lead:transfer:region"
CB_LEAD_TRANSFER_DEALER = "sales:lead:transfer:dealer"
CB_LEAD_TRANSFER_CONFIRM = "sales:lead:transfer:confirm"
CB_LEAD_REQUEST_APPROVAL = "sales:lead:reqapproval"
CB_LEAD_KEEP = "sales:lead:keep"
CB_LEAD_REJECT = "sales:lead:reject"

CB_DIRECTORY_REGION = "sales:dir:region"
CB_DIRECTORY_DEALER = "sales:dir:dealer"


# Регионы могут содержать любые символы — callback_data ≤ 64 байт.
# Передаём короткий хэш + храним соответствие в FSM/context.
def region_token(region: str) -> str:
    return hashlib.md5(region.encode()).hexdigest()[:10]


def sales_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Новые лиды", callback_data=SalesMenuCallback.LEADS_NEW
                ),
                InlineKeyboardButton(
                    text="⚙️ В работе", callback_data=SalesMenuCallback.LEADS_IN_PROGRESS
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📨 Переданы диллеру",
                    callback_data=SalesMenuCallback.LEADS_TRANSFERRED,
                ),
                InlineKeyboardButton(
                    text="📍 Найти диллера", callback_data=SalesMenuCallback.FIND_DEALER
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤖 ИИ-помощник", callback_data=SalesMenuCallback.ASSISTANT
                ),
            ],
        ]
    )


def head_of_sales_main_menu() -> InlineKeyboardMarkup:
    """Меню HeadOfSales = sales-меню + очередь согласований."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Новые лиды", callback_data=SalesMenuCallback.LEADS_NEW
                ),
                InlineKeyboardButton(
                    text="⚙️ В работе", callback_data=SalesMenuCallback.LEADS_IN_PROGRESS
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📨 Переданы диллеру",
                    callback_data=SalesMenuCallback.LEADS_TRANSFERRED,
                ),
                InlineKeyboardButton(
                    text="📍 Найти диллера", callback_data=SalesMenuCallback.FIND_DEALER
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤖 ИИ-помощник", callback_data=SalesMenuCallback.ASSISTANT
                ),
                InlineKeyboardButton(
                    text="👔 Очередь согласований", callback_data=SalesMenuCallback.HOS_QUEUE
                ),
            ],
        ]
    )


def hos_queue_list_kb(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    from bot.api.keyboards import truncate

    rows = [
        [
            InlineKeyboardButton(
                text=truncate(label), callback_data=f"{CB_HOS_VIEW}:{aid}"
            )
        ]
        for aid, label in items
    ]
    rows.append(
        [InlineKeyboardButton(text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hos_approval_actions_kb(approval_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить", callback_data=f"{CB_HOS_APPROVE}:{approval_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"{CB_HOS_REJECT}:{approval_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ К очереди", callback_data=SalesMenuCallback.HOS_QUEUE
                )
            ],
        ]
    )


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU
                )
            ]
        ]
    )


def leads_list_kb(items: list[tuple[int, str]], back: str) -> InlineKeyboardMarkup:
    from bot.api.keyboards import truncate

    rows = [
        [
            InlineKeyboardButton(
                text=truncate(label), callback_data=f"{CB_LEAD_VIEW}:{lid}"
            )
        ]
        for lid, label in items
    ]
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lead_actions_kb(lead_id: int, status: RequestStatus) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == RequestStatus.NEW:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Взять в работу", callback_data=f"{CB_LEAD_TAKE}:{lead_id}"
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"{CB_LEAD_REJECT}:{lead_id}"
                )
            ]
        )
    elif status == RequestStatus.IN_PROGRESS:
        rows.append(
            [
                InlineKeyboardButton(
                    text="📨 Передать диллеру",
                    callback_data=f"{CB_LEAD_TRANSFER_REGION}:{lead_id}",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"{CB_LEAD_REJECT}:{lead_id}"
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def regions_kb(
    regions: list[str], *, callback_prefix: str, lead_id: int | None = None
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for region in regions:
        token = region_token(region)
        cb = (
            f"{callback_prefix}:{lead_id}:{token}"
            if lead_id is not None
            else f"{callback_prefix}:{token}"
        )
        rows.append([InlineKeyboardButton(text=region, callback_data=cb)])
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dealers_kb(
    dealers: list[tuple[int, str]], *, lead_id: int | None = None
) -> InlineKeyboardMarkup:
    """Список дилеров → клик ведёт в карточку (передача делается из карточки).

    Если lead_id указан — карточка откроется в режиме «передача лида».
    """
    rows: list[list[InlineKeyboardButton]] = []
    for dealer_id, name in dealers:
        cb = (
            f"{CB_DIRECTORY_DEALER}:{lead_id}:{dealer_id}"
            if lead_id is not None
            else f"{CB_DIRECTORY_DEALER}:0:{dealer_id}"
        )
        rows.append([InlineKeyboardButton(text=name, callback_data=cb)])
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dealer_card_actions_kb(
    *,
    dealer_id: int,
    lead_id: int | None,
    tg_url: str | None,
    head_available: bool = False,
) -> InlineKeyboardMarkup:
    """Действия в карточке диллера. lead_id=None → режим справочника (только TG)."""
    rows: list[list[InlineKeyboardButton]] = []

    if lead_id is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Передать сюда лид",
                    callback_data=f"{CB_LEAD_TRANSFER_CONFIRM}:{lead_id}:{dealer_id}",
                )
            ]
        )

    if tg_url is not None:
        rows.append([InlineKeyboardButton(text="💬 Написать в TG", url=tg_url)])

    if lead_id is not None and head_available:
        rows.append(
            [
                InlineKeyboardButton(
                    text="👔 Запросить согласование руководителя",
                    callback_data=f"{CB_LEAD_REQUEST_APPROVAL}:{lead_id}:{dealer_id}",
                )
            ]
        )

    if lead_id is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔒 Оставить лид у себя",
                    callback_data=f"{CB_LEAD_KEEP}:{lead_id}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dealer_tg_url(*, username: str | None, telegram_id: int) -> str | None:
    """Прямая ссылка в TG. `https://t.me/<username>` или `tg://user?id=<id>`."""
    if username:
        return f"https://t.me/{username}"
    if telegram_id:
        return f"tg://user?id={telegram_id}"
    return None
