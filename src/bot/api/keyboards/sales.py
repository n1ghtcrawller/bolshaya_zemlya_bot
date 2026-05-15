import hashlib

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.core.enums import RequestStatus


class SalesMenuCallback:
    LEADS_NEW = "sales:leads:new"
    LEADS_IN_PROGRESS = "sales:leads:in_progress"
    LEADS_TRANSFERRED = "sales:leads:transferred"
    FIND_DEALER = "sales:dealer:find"
    ASSISTANT = "sales:ai"
    BACK_TO_MENU = "sales:back_to_menu"


CB_LEAD_VIEW = "sales:lead:view"
CB_LEAD_TAKE = "sales:lead:take"
CB_LEAD_TRANSFER_REGION = "sales:lead:transfer:region"
CB_LEAD_TRANSFER_DEALER = "sales:lead:transfer:dealer"
CB_LEAD_REJECT = "sales:lead:reject"

CB_DIRECTORY_REGION = "sales:dir:region"


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


def leads_list_kb(lead_ids: list[int], back: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Открыть #{lid}", callback_data=f"{CB_LEAD_VIEW}:{lid}")]
        for lid in lead_ids
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


def dealers_kb(dealers: list[tuple[int, str]], lead_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=name, callback_data=f"{CB_LEAD_TRANSFER_DEALER}:{lead_id}:{dealer_id}"
            )
        ]
        for dealer_id, name in dealers
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ В меню", callback_data=SalesMenuCallback.BACK_TO_MENU
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
