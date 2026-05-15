"""Тексты сообщений. Вынесены отдельно для лёгкой правки и будущего i18n."""

GREETING_NEW = (
    "👋 Привет, {name}!\n\n"
    "Это бот проекта «Большая Земля». Выбери раздел из меню ниже."
)
GREETING_RETURNING = "С возвращением, {name}! Выбери раздел из меню."

# Client menu
CLIENT_MENU_HEADER = "🟢 Главное меню"
CLIENT_MENU_HINT = "Раздел в разработке — скоро будет доступно."

# Profile
PROFILE_HEADER = "👤 Профиль"
PROFILE_TEMPLATE = (
    "👤 Профиль\n\n"
    "Имя: {full_name}\n"
    "Телефон: {phone}\n"
    "Регион: {region}\n"
    "Организация: {company}\n"
    "Email: {email}"
)
PROFILE_EMPTY_VALUE = "—"

# Requests list
REQUESTS_EMPTY = "У вас пока нет заявок. Нажмите «Оставить заявку», чтобы создать первую."
REQUEST_LIST_HEADER = "📋 Ваши заявки:"
REQUEST_LINE = "#{id} · {status} · {created_at:%d.%m.%Y %H:%M}"
REQUEST_DETAILS = (
    "📋 Заявка #{id}\n"
    "Статус: {status}\n"
    "Создана: {created_at:%d.%m.%Y %H:%M}\n\n"
    "Контактное лицо: {contact_name}\n"
    "Телефон: {contact_phone}\n\n"
    "Комментарий:\n{comment}"
)

# Create request FSM
REQUEST_ASK_NAME = "Как к вам обращаться? (имя и фамилия)"
REQUEST_ASK_PHONE = (
    "Укажите контактный телефон.\n"
    "Можно отправить кнопкой «📱 Поделиться контактом» или написать вручную."
)
REQUEST_ASK_COMMENT = (
    "Опишите кратко, по какому вопросу вы обращаетесь. "
    "Если не хотите указывать — отправьте «-»."
)
REQUEST_CONFIRM = (
    "Проверьте, всё ли верно:\n\n"
    "Имя: {contact_name}\n"
    "Телефон: {contact_phone}\n"
    "Комментарий: {comment}\n\n"
    "Подтвердить отправку?"
)
REQUEST_CREATED = "✅ Заявка #{id} создана. Менеджер свяжется с вами."
REQUEST_CANCELLED = "Создание заявки отменено."
REQUEST_VALIDATION_FAILED = "Не удалось распознать значение, попробуйте ещё раз."

STATUS_LABELS = {
    "new": "🆕 новая",
    "in_progress": "⚙️ в работе",
    "transferred_to_dealer": "📨 передана диллеру",
    "done": "✅ выполнена",
    "rejected": "❌ отклонена",
}

# Dealer
DEALER_MENU_HEADER = "🟠 Кабинет диллера"
DEALER_LEADS_EMPTY = "Активных лидов пока нет."
DEALER_LEADS_HEADER = "📥 Новые лиды ({total})"
DEALER_LEAD_LINE = "#{id} · {status} · {created_at:%d.%m.%Y %H:%M}\n   {contact_name} · {contact_phone}"
DEALER_LEAD_DETAILS = (
    "📥 Лид #{id}\n"
    "Статус: {status}\n"
    "Получен: {created_at:%d.%m.%Y %H:%M}\n\n"
    "Контактное лицо: {contact_name}\n"
    "Телефон: {contact_phone}\n\n"
    "Комментарий:\n{comment}"
)
DEALER_LEAD_NOT_FOUND = "Лид не найден или не назначен на вас."
DEALER_LEAD_STATUS_UPDATED = "Статус лида #{id} обновлён: {status}."

DEALER_STATS_HEADER = "📊 Статистика по вашим лидам"
DEALER_STATS_TEMPLATE = (
    "📊 Статистика\n\n"
    "Всего: {total}\n"
    "🆕 Новых: {new}\n"
    "⚙️ В работе: {in_progress}\n"
    "✅ Выполнено: {done}\n"
    "❌ Отклонено: {rejected}"
)

DEALER_MATERIALS_HEADER = "📚 Продающие материалы\nВыберите раздел:"
DEALER_MATERIALS_EMPTY = "В этом разделе пока нет материалов."
DEALER_MATERIAL_NOT_FOUND = "Материал не найден."

DEALER_SERVICE_REQUESTS_EMPTY = (
    "🔧 Сервисных обращений пока нет.\n"
    "Клиенты смогут отправлять обращения после релиза раздела «Сервис и запчасти»."
)

DEALER_PROFILE_HEADER = "👤 Профиль диллера"
DEALER_PROFILE_TEMPLATE = (
    "👤 Профиль диллера\n\n"
    "Имя: {full_name}\n"
    "Компания: {company}\n"
    "Регион: {region}\n"
    "Адрес: {address}\n"
    "Телефон: {phone}\n\n"
    "О себе:\n{description}"
)
DEALER_PROFILE_EMPTY_VALUE = "—"
DEALER_PROFILE_EDIT_HINT = "Выберите поле для редактирования:"
DEALER_PROFILE_ASK_PHONE = "Введите контактный телефон или отправьте «-» чтобы очистить."
DEALER_PROFILE_ASK_COMPANY = "Введите название компании или отправьте «-» чтобы очистить."
DEALER_PROFILE_ASK_REGION = "Введите регион работы или отправьте «-» чтобы очистить."
DEALER_PROFILE_ASK_ADDRESS = "Введите адрес офиса/точки или отправьте «-» чтобы очистить."
DEALER_PROFILE_ASK_DESCRIPTION = "Введите описание (о себе/о компании) или отправьте «-» чтобы очистить."
DEALER_PROFILE_FIELD_SAVED = "Поле сохранено."

MATERIAL_CATEGORY_LABELS = {
    "catalogs": "📕 Каталоги",
    "photos_videos": "🖼 Фото / Видео",
    "presentations": "📊 Презентации",
    "templates": "📝 Шаблоны",
    "training": "🎓 Обучение по продукту",
}

# Sales
SALES_MENU_HEADER = "🔵 Кабинет Sales"
SALES_LEADS_NEW_EMPTY = "Новых лидов в очереди нет."
SALES_LEADS_NEW_HEADER = "📥 Новые лиды ({total})"
SALES_LEADS_IN_PROGRESS_EMPTY = "У вас нет лидов в работе."
SALES_LEADS_IN_PROGRESS_HEADER = "⚙️ В работе ({total})"
SALES_LEADS_TRANSFERRED_EMPTY = "Вы пока никому не передавали лиды."
SALES_LEADS_TRANSFERRED_HEADER = "📨 Переданы диллерам ({total})"

SALES_LEAD_DETAILS = (
    "📥 Лид #{id}\n"
    "Статус: {status}\n"
    "Создан: {created_at:%d.%m.%Y %H:%M}\n\n"
    "Клиент: {contact_name}\n"
    "Телефон: {contact_phone}\n\n"
    "Комментарий:\n{comment}"
)
SALES_LEAD_NOT_FOUND = "Лид не найден."
SALES_LEAD_TAKEN = "✅ Лид #{id} взят в работу."
SALES_LEAD_ALREADY_TAKEN = "Этот лид уже забрал другой Sales."
SALES_LEAD_REJECTED = "❌ Лид #{id} отклонён."
SALES_LEAD_TRANSFER_PICK_REGION = "Выберите регион диллера:"
SALES_LEAD_TRANSFER_NO_REGIONS = (
    "В справочнике нет дилеров с указанным регионом.\n"
    "Попросите дилеров заполнить регион в профиле."
)
SALES_LEAD_TRANSFER_NO_DEALERS = "В выбранном регионе нет активных дилеров."
SALES_LEAD_TRANSFER_PICK_DEALER = "Выберите диллера в регионе «{region}»:"
SALES_LEAD_TRANSFER_DONE = "📨 Лид #{id} передан диллеру: {dealer_name}."
SALES_LEAD_TRANSFER_NOT_OWNER = "Передать можно только лид, который вы взяли в работу."

SALES_FIND_DEALER_HEADER = "📍 Найти диллера\nВыберите регион:"
SALES_FIND_DEALER_NO_REGIONS = (
    "Дилеры пока не заполнили регион в профиле — справочник пуст."
)
SALES_DEALER_CARD = (
    "📍 {full_name}\n"
    "Компания: {company}\n"
    "Регион: {region}\n"
    "Адрес: {address}\n"
    "Телефон: {phone}\n"
    "Telegram: @{username}\n\n"
    "{description}"
)
SALES_DEALER_CARD_NO_USERNAME = "—"

SALES_ASSISTANT_HEADER = (
    "🤖 ИИ-помощник Sales\n\n"
    "Опишите вопрос или ситуацию по клиенту — пришлю подсказку через n8n.\n"
    "Для выхода нажмите «✖️ Отмена»."
)
SALES_ASSISTANT_THINKING = "🤖 Думаю..."
SALES_ASSISTANT_ANSWER_HEADER = "🤖 Подсказка:"
SALES_ASSISTANT_UNAVAILABLE = (
    "ИИ-помощник временно недоступен. Попробуйте позже или обратитесь к админу."
)

# Marketing
MKT_MENU_HEADER = "🟣 Кабинет Маркетинг / Админ"

MKT_DASHBOARD_TEMPLATE = (
    "📊 Дашборд\n\n"
    "<b>Пользователи по ролям</b>\n"
    "{users_block}\n\n"
    "<b>Лиды по статусам</b>\n"
    "{leads_block}"
)
MKT_DASHBOARD_EMPTY_USERS = "Пока нет пользователей."
MKT_DASHBOARD_EMPTY_LEADS = "Пока нет лидов."

MKT_USERS_PICK_ROLE = "Выберите роль для просмотра пользователей:"
MKT_USERS_LIST_HEADER = "{role}: всего {total}"
MKT_USER_CARD = (
    "👤 #{id} {full_name}\n"
    "TG: @{username} (id={telegram_id})\n"
    "Роль: {role}\n"
    "Регистрация: {created_at:%d.%m.%Y}"
)
MKT_USER_NOT_FOUND = "Пользователь не найден."
MKT_USER_PICK_NEW_ROLE = "Выберите новую роль для {full_name}:"
MKT_USER_ROLE_UPDATED = "Роль пользователя {full_name} изменена на {role}."

ROLE_LABELS = {
    "client": "Клиент",
    "dealer": "Диллер",
    "sales": "Sales",
    "marketing": "Маркетинг",
}

MKT_MATERIALS_PICK_CATEGORY = "Выберите категорию для нового материала:"
MKT_MATERIALS_ASK_FILE = (
    "Отправьте файл, фото, видео или GIF (как медиа, а не как пересланное сообщение)."
)
MKT_MATERIALS_ASK_TITLE = "Введите название материала:"
MKT_MATERIALS_ASK_DESCRIPTION = "Введите описание или «-» чтобы пропустить:"
MKT_MATERIALS_CREATED = "✅ Материал #{id} «{title}» добавлен в раздел «{category}»."

MKT_BROADCAST_ASK_TEXT = (
    "Введите текст рассылки (либо «-» чтобы отправить только медиа):"
)
MKT_BROADCAST_ASK_MEDIA = (
    "Прикрепите медиа (фото/видео/документ/GIF) или отправьте «-» чтобы пропустить."
)
MKT_BROADCAST_ASK_SEGMENT = "Выберите сегмент получателей:"
MKT_BROADCAST_CONFIRM = (
    "📣 Рассылка\n\n"
    "Сегмент: {segment}\n"
    "Получателей: {recipients}\n"
    "Медиа: {media}\n\n"
    "{text}\n\n"
    "Отправить?"
)
MKT_BROADCAST_QUEUED = "📣 Рассылка #{id} отправлена в n8n. Доставка: {count} получателей."
MKT_BROADCAST_FAILED = "Не удалось отправить рассылку: {error}"
MKT_BROADCAST_LIST_HEADER = "📣 Последние рассылки:"
MKT_BROADCAST_LIST_LINE = "#{id} · {status} · {created_at:%d.%m.%Y %H:%M} · отпр.: {sent_count}"
MKT_BROADCAST_VALIDATION = "Нужен текст или медиа — пустую рассылку не отправляем."

MKT_CONTENT_PICK_TYPE = "Выберите тип контент-записи:"
MKT_CONTENT_LIST_HEADER = "{type_label}: записей {total}"
MKT_CONTENT_LIST_EMPTY = "В этом разделе пока пусто."
MKT_CONTENT_ASK_TITLE = "Введите заголовок:"
MKT_CONTENT_ASK_BODY = "Введите тело записи или «-» чтобы пропустить:"
MKT_CONTENT_ASK_REGION = "Введите регион (для адаптаций) или «-» чтобы пропустить:"
MKT_CONTENT_ASK_SCHEDULED = (
    "Дата публикации в формате ДД.ММ.ГГГГ ЧЧ:ММ "
    "или «-» чтобы оставить без расписания:"
)
MKT_CONTENT_CREATED = "✅ Запись #{id} «{title}» создана."
MKT_CONTENT_DATE_INVALID = "Не удалось распознать дату. Попробуйте ещё раз."

CONTENT_TYPE_LABELS = {
    "plan": "🗓 Контент-план",
    "idea": "💡 Идеи",
    "regional": "📍 Адаптации по регионам",
    "scheduled": "⏰ Отложка",
}
CONTENT_STATUS_LABELS = {
    "draft": "✍️ черновик",
    "scheduled": "⏰ запланирована",
    "published": "📢 опубликована",
    "archived": "🗄 в архиве",
}

MKT_EXPO_LIST_HEADER = "🎪 Ближайшие выставки:"
MKT_EXPO_LIST_EMPTY = "Запланированных выставок пока нет."
MKT_EXPO_LIST_LINE = "#{id} · {starts_at:%d.%m.%Y} · {title}"
MKT_EXPO_DETAILS = (
    "🎪 #{id} {title}\n"
    "Локация: {location}\n"
    "Даты: {dates}\n\n"
    "Продукты:\n{products}\n\n"
    "Описание:\n{description}"
)
MKT_EXPO_ASK_TITLE = "Название выставки:"
MKT_EXPO_ASK_LOCATION = "Локация (город / площадка) или «-»:"
MKT_EXPO_ASK_STARTS = "Дата начала ДД.ММ.ГГГГ:"
MKT_EXPO_ASK_ENDS = "Дата окончания ДД.ММ.ГГГГ или «-» если такая же:"
MKT_EXPO_ASK_PRODUCTS = "Продукты на стенде (списком через запятую) или «-»:"
MKT_EXPO_ASK_DESCRIPTION = "Описание/задачи или «-»:"
MKT_EXPO_CREATED = "✅ Выставка #{id} «{title}» добавлена."

MKT_EXPO_ASSISTANT_HEADER = (
    "🤖 ИИ-помощник Выставки\n\n"
    "Спросите про планирование стенда, продукты, мероприятия — пришлю подсказку через n8n.\n"
    "Для выхода нажмите «✖️ Отмена»."
)
MKT_EXPO_ASSISTANT_UNAVAILABLE = SALES_ASSISTANT_UNAVAILABLE

# Catalog (Client + shared)
CATALOG_EMPTY = (
    "Каталог пока пуст. Маркетинг ещё не загрузил товары."
)
CATALOG_HEADER = "📚 Каталог продукции\nВыберите категорию:"
CATALOG_PICKER_HEADER = (
    "🔍 Подбор техники\n\n"
    "Выберите категорию — покажу подходящие модели. "
    "Расширенный подбор по параметрам в разработке."
)
CATALOG_CATEGORY_HEADER = "📂 {name} · товаров {total}"
CATALOG_CATEGORY_EMPTY = "В этой категории пока нет товаров."
CATALOG_PRODUCT_NOT_FOUND = "Товар не найден или снят с продажи."
CATALOG_PRODUCT_TEMPLATE = (
    "<b>{name}</b>\n"
    "Категория: {category}\n"
    "Цена: {price}\n"
    "\n{short}\n{full}\n"
    "\n<b>Характеристики</b>\n{specs}"
)
CATALOG_REQUEST_NOTE_PREFIX = "Интересует товар «{name}» (#{id})."

# Catalog admin (Marketing)
MKT_CATALOG_MENU = "📚 Каталог продукции"
MKT_CATALOG_HEADER = "📚 Каталог продукции\nКатегорий: {categories_total}"
MKT_CATALOG_NEW_CATEGORY = "✍️ Введите название новой категории:"
MKT_CATALOG_CATEGORY_CREATED = "✅ Категория «{name}» создана (id={id})."
MKT_CATALOG_PICK_CATEGORY_FOR_PRODUCT = "Выберите категорию, в которую добавить товар:"
MKT_CATALOG_PRODUCT_ASK_NAME = "Название товара:"
MKT_CATALOG_PRODUCT_ASK_SHORT = "Краткое описание (1 строка) или «-»:"
MKT_CATALOG_PRODUCT_ASK_FULL = "Подробное описание или «-»:"
MKT_CATALOG_PRODUCT_ASK_PRICE = "Цена (текстом, например «от 1 200 000 ₽») или «-»:"
MKT_CATALOG_PRODUCT_ASK_SPECS = "Характеристики (можно с переносами) или «-»:"
MKT_CATALOG_PRODUCT_ASK_PHOTO = (
    "Пришлите главное фото товара или отправьте «-» чтобы добавить без фото."
)
MKT_CATALOG_PRODUCT_CREATED = "✅ Товар «{name}» (id={id}) добавлен в категорию «{category}»."
MKT_CATALOG_NO_CATEGORIES = "Сначала создайте хотя бы одну категорию."
