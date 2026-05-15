from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CB_CATEGORY = "cat:c"
CB_PRODUCT = "cat:p"
CB_PRODUCT_PAGE = "cat:pp"
CB_PRODUCT_REQUEST = "cat:req"
CB_BACK_TO_CATEGORIES = "cat:categories"


def categories_kb(
    categories: list[tuple[int, str]], *, back_callback: str
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"{CB_CATEGORY}:{cid}")]
        for cid, name in categories
    ]
    rows.append([InlineKeyboardButton(text="◀️ В меню", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_page_kb(
    category_id: int,
    page: int,
    pages: int,
    product_ids: list[int],
    *,
    back_callback: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for pid in product_ids:
        rows.append(
            [InlineKeyboardButton(text=f"Открыть #{pid}", callback_data=f"{CB_PRODUCT}:{pid}")]
        )
    if pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="◀️", callback_data=f"{CB_PRODUCT_PAGE}:{category_id}:{page - 1}"
                )
            )
        nav.append(
            InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="cat:noop")
        )
        if page < pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text="▶️", callback_data=f"{CB_PRODUCT_PAGE}:{category_id}:{page + 1}"
                )
            )
        rows.append(nav)
    rows.append(
        [InlineKeyboardButton(text="◀️ К категориям", callback_data=CB_BACK_TO_CATEGORIES)]
    )
    rows.append([InlineKeyboardButton(text="🏠 В меню", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_card_kb(
    product_id: int, category_id: int, *, back_callback: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Оставить заявку на этот товар",
                    callback_data=f"{CB_PRODUCT_REQUEST}:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ К списку", callback_data=f"{CB_CATEGORY}:{category_id}"
                ),
            ],
            [InlineKeyboardButton(text="🏠 В меню", callback_data=back_callback)],
        ]
    )
