# Bot «Большая Земля»

Телеграм-бот по проекту «Большая Земля». Стек: **aiogram 3**, **SQLAlchemy 2 (async) + PostgreSQL/asyncpg**, **Redis** (FSM + кэш ролей), **pydantic v2**, **httpx** (вызов n8n).

## Архитектура (слои)

```
TG API (handlers, keyboards, middlewares)
        │
        ▼
  Service слой (бизнес-логика, n8n клиент)
        │
        ├──► Redis (FSM state, кэш ролей)
        ▼
  CRUD слой (repositories) ──► PostgreSQL
```

Соответствие слоёв с Figma-доской (`Архитектура` → `Слои приложения`):

| Доска                            | Папка                            |
| -------------------------------- | -------------------------------- |
| TG API СЛОЙ (Клиентская часть)   | `src/bot/api/`                   |
| REDIS СЛОЙ (хранение кэша)       | `src/bot/cache/`                 |
| SERVICE СЛОЙ (обработка ошибок)  | `src/bot/services/`              |
| CRUD СЛОЙ (взаимодействие с СУБД)| `src/bot/db/repositories/`       |
| СУБД (хранение данных)           | `src/bot/db/models/` + Postgres  |
| n8n                              | `src/bot/services/n8n_client.py` |

## Запуск

### 1. Зависимости

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

### 2. PostgreSQL и Redis через docker-compose

```powershell
copy .env.example .env
# отредактируйте BOT_TOKEN и при необходимости креды БД/Redis
docker compose up -d
```

### 3. Применить миграции

```powershell
alembic upgrade head
```

### 4. Запустить бот

```powershell
python -m bot
```

## Что реализовано

### Итерация 1 — скелет + роль Клиент

- Полная слоистая структура (API / Service / Cache / CRUD / Models)
- Конфиг через `pydantic-settings` (`.env`)
- Engine + sessionmaker для PostgreSQL, sessions выдаются через `DbSessionMiddleware`
- Redis-клиент: `RoleCache` (TTL 30 мин) и `RedisStorage` для FSM
- Middleware `RoleMiddleware`: определяет роль по telegram_id, авто-создаёт пользователя как `client` при первом `/start`
- `N8nClient` — обёртка над `httpx`, эндпоинты в `.env` (пока заглушки)
- Меню **роли Клиент**:
  - 👤 Профиль (просмотр)
  - 📋 Мои заявки (список + детальный просмотр)
  - 📝 Оставить заявку (FSM: имя → телефон с «Поделиться контактом» → комментарий → подтверждение)
  - Заглушки: Каталог, Подобрать технику, Найти диллера, Сервис и запчасти, Чат с менеджером, Заказать звонок

### Итерация 2 — роль Диллер

- 📥 **Новые лиды** — список лидов со статусом `transferred_to_dealer` / `in_progress`, назначенных текущему дилеру; смена статуса: «Взять в работу» → «Выполнено» / «Отклонить»
- 📚 **Продающие материалы** — 5 категорий (Каталоги, Фото/Видео, Презентации, Шаблоны, Обучение по продукту), пагинация, отдача файла по `telegram_file_id` (document / photo / video / animation)
- 📊 **Статистика** — счётчики по статусам своих лидов
- 👤 **Профиль диллера** — отдельная таблица `dealer_profiles` (телефон, компания, регион, адрес, описание); FSM редактирования по одному полю, "-" очищает значение
- 🔧 **Сервисные обращения** — пока заглушка (создание со стороны Клиента появится отдельной итерацией)

### Итерация 3 — роль Sales

- 📥 **Новые лиды** — общая очередь со `status=new` (без `assigned_sales_id`/`assigned_dealer_id`)
- ⚙️ **В работе** — только свои лиды (status=in_progress, assigned_sales_id=current)
- 📨 **Переданы диллеру** — свои лиды status=transferred_to_dealer
- 📍 **Найти диллера** — справочник по регионам из заполненных `dealer_profiles`
- 🤖 **ИИ-помощник Sales** — FSM-сценарий: вопрос → `N8nClient.sales_assistant` → ответ. Graceful fallback если n8n недоступен.
- Жизненный цикл лида: Клиент создаёт → Sales берёт в работу → Sales выбирает регион → выбирает диллера → лид уходит дилеру (тот видит его в «Новых лидах» из итерации 2)
- Контроль доступа: передавать может только тот Sales, кто этот лид взял

### Итерация 4 — роль Маркетинг / Админ

- 📊 **Дашборд** — текстовая сводка: пользователи по ролям, лиды по статусам (агрегаты SQL)
- 👥 **Пользователи** — список по ролям → карточка → смена роли. При смене инвалидируется Redis-кэш (`RoleCache.invalidate`), новая роль работает сразу на следующее сообщение
- 📚 **Материалы (загрузка)** — FSM: категория → файл (document/photo/video/animation) → название → описание. `file_id` пишется в `sales_materials`, дилеры видят материал в своём подменю немедленно
- 📣 **Рассылки** — FSM: текст → медиа (опц.) → сегмент (роль или «все») → подтверждение → отправка в `N8nClient.broadcast`; статус и счётчик сохраняются в `broadcasts`. История доступна из меню рассылок
- 📝 **Контент** — простые записи 4 типов (план/идея/региональная/отложка) с заголовком, телом, регионом и датой публикации; чтение по типу
- 🎪 **Выставки** — ближайшие, карточка, создание (название/локация/даты/продукты/описание)
- 🤖 **ИИ-помощник Выставки** — `N8nClient.expo_assistant`, тот же паттерн что у Sales-ассистента

### Итерация 14 — тесты

Покрыта критичная бизнес-логика: **30 тестов, все проходят** за ~1 сек.

Стек: `pytest` + `pytest-asyncio` (auto mode) + `aiosqlite` (in-memory SQLite, чистая БД на каждый тест). Фабрика `make_user(role=...)` с автоинкрементом `telegram_id`.

```
tests/
├── conftest.py
├── unit/
│   ├── test_catalog_admin_service.py  — slugify, уникальность slug
│   ├── test_approval_policy.py        — fallback head_of_marketing → marketer
│   ├── test_content_service.py        — выбор статуса при create
│   └── test_sales_lead_service.py     — take/transfer/keep/reject с проверкой доступа
└── integration/
    ├── test_lead_approval_flow.py     — request → approve → реальная передача
    ├── test_client_request_repository.py
    ├── test_sales_material_repository.py
    ├── test_dealer_directory_repository.py
    └── test_dashboard_service.py      — snapshot, dealers_breakdown, top_products
```

Запуск:
```powershell
pip install -e ".[dev]"
pytest -q
```

Что **не** покрыто (отложено): тесты aiogram-хендлеров (требуют мок-Bot и эмуляции апдейтов), тесты `N8nClient` с моком httpx, тесты `content_publisher` (через freezegun).

### Итерация 13 — готовые n8n workflow

Папка [n8n/](n8n/) с готовыми JSON-файлами и инструкцией. Поднимаются 4 workflow:

| Файл | Webhook path | Что делает |
|---|---|---|
| [sales_assistant.json](n8n/workflows/sales_assistant.json) | `/webhook/sales-assistant` | LLM-помощник Sales (OpenAI gpt-4o-mini) |
| [expo_assistant.json](n8n/workflows/expo_assistant.json)   | `/webhook/expo-assistant`  | LLM-помощник по выставкам |
| [broadcast.json](n8n/workflows/broadcast.json)             | `/webhook/broadcast`       | Массовая рассылка: Split Out по recipients → Switch по file_type → 5 веток Telegram (sendMessage / Photo / Video / Document / Animation) |
| [content_publish.json](n8n/workflows/content_publish.json) | `/webhook/content-publish` | Автопостинг в Telegram-канал из `$vars.PUBLISH_CHANNEL_ID` |

В [n8n/README.md](n8n/README.md) — пошаговая инструкция: импорт через UI, настройка Telegram/OpenAI credentials, переменные окружения n8n. В [n8n/test/](n8n/test/) — `curl`-скрипты для ручной проверки каждого webhook без бота. В n8n/README также есть готовый блок для `docker-compose.yml`, если n8n нужно поднять рядом с ботом.

### Итерация 12 — аналитика по дилерам и продуктам

Расширен раздел «📊 Дашборд» у Маркетинга. Раньше это был один экран, теперь — подменю:

- **📋 Сводка** — старый отчёт (пользователи по ролям + лиды по статусам)
- **📍 По диллерам** — топ-10 дилеров по числу назначенных лидов. По каждому: всего · в работе · выполнено · отклонено · передано
- **📦 По продуктам** — топ-10 товаров по числу заявок (категория + название)

Для аналитики по продуктам:
- Добавлено поле `client_requests.product_id` (миграция 0010) — nullable FK на `products.id` (ON DELETE SET NULL)
- В клиентском «Оставить заявку на этот товар» из карточки товара `product_id` пробрасывается через FSM-state в `ClientRequestCreate` и сохраняется в лиде
- `DashboardService.top_products` строит топ через `GROUP BY product_id` с JOIN на `products` и `product_categories`
- `DashboardService.dealers_breakdown` использует `CASE WHEN ... THEN 1 ELSE 0` для подсчёта по статусам в одном запросе

История лидов до миграции остаётся без `product_id` (NULL) — это нормально: в топ-продуктов попадут только заявки, созданные после деплоя.

### Итерация 11 — автопостинг запланированного контента

В bot-процесс добавлен фоновый воркер на `APScheduler.AsyncIOScheduler`, который раз в `PUBLISHER_INTERVAL_SECONDS` (по умолчанию 60 сек) обходит `content_items` со `status in (scheduled, approved)` и `scheduled_at <= now`, отдаёт каждый в n8n webhook `N8N_WEBHOOK_CONTENT_PUBLISH` и при успехе ставит статус `published`.

- Новый сервис [content_publisher.py](src/bot/services/content_publisher.py): `publish_due_content(sessionmaker, n8n)` — один цикл публикации
- [ContentItemRepository.list_due_for_publish](src/bot/db/repositories/content_item.py)
- [N8nClient.content_publish](src/bot/services/n8n_client.py)
- Запуск/остановка scheduler-а в [__main__.py](src/bot/__main__.py) (graceful shutdown)
- Конфиг: `PUBLISHER_ENABLED` (`true`/`false`) и `PUBLISHER_INTERVAL_SECONDS` в `.env`
- Защита: `max_instances=1, coalesce=True` — параллельные тики одного job не запускаются, накопившиеся выполнения схлопываются в один
- Времена везде UTC (модель хранит `DateTime(timezone=True)`, scheduler стартует в UTC)
- Логика статуса при создании поправлена: теперь `SCHEDULED` ставится **только если** есть `scheduled_at`. Тип контента `ContentType.SCHEDULED` («отложка») — отдельная ось, статус не определяет

### Итерация 10 — эскалация на руководящие роли

Две новые роли: `HEAD_OF_SALES`, `HEAD_OF_MARKETING`. Меняют процессы согласования.

**A. Эскалация передачи лидов (Sales → HeadOfSales):**
- Новая модель `LeadApproval` (lead_id, sales_user_id, proposed_dealer_id, status, decision_by_user_id, decision_at, decision_note) — миграция 0009
- В карточке диллера у Sales появляется кнопка «👔 Запросить согласование руководителя» — **только если** в БД есть хотя бы один пользователь с ролью `head_of_sales`
- Нажатие создаёт `pending`-запрос; повторный запрос по тому же лиду блокируется (`SALES_LEAD_APPROVAL_DUPLICATE`)
- HeadOfSales имеет своё меню = меню Sales + новый пункт «👔 Очередь согласований»:
  - Список pending → карточка с деталями (лид + sales + предлагаемый дилер) → «✅ Одобрить» / «❌ Отклонить»
  - При одобрении лид реально передаётся (`assigned_dealer_id` + `status=transferred_to_dealer`) от имени sales-автора
  - При отклонении лид остаётся у sales в `in_progress`

**B. Эскалация согласований Маркетинга:**
- `RoleFilter` маркетингового роутера расширен до `MARKETING | HEAD_OF_MARKETING` — оба видят одно и то же меню
- Хелпер [approval_policy.py](src/bot/services/approval_policy.py): `can_approve_marketing(session, user)` — `True` только для head_of_marketing; **fallback** к обычному маркетологу, если head в БД отсутствует (чтобы очередь не зависла, пока роль не назначена)
- Защита применена в двух местах:
  - Одобрение/отклонение контента (`pending_approval` → approved/rejected) в [content.py](src/bot/api/handlers/marketing/content.py)
  - Модерация локальных материалов дилеров в [moderation.py](src/bot/api/handlers/marketing/moderation.py)
- Кнопки одобрения всем по-прежнему видны (UX), но при нажатии без прав — мягкое сообщение

### Итерация 9 — клиентское «Найти диллера» (последняя заглушка закрыта)

Раздел Клиента «📍 Найти диллера» переиспользует существующий `DealerDirectoryService` (общий с Sales).

- Список регионов (только дилеры с заполненным регионом) → выбор → список дилеров в регионе → **карточка** (имя, компания, регион, адрес, телефон, специализация, описание)
- Из карточки три действия (по ответу заказчика #2):
  - **💬 Написать в TG** — URL-кнопка `https://t.me/<username>` (fallback `tg://user?id=<id>`)
  - **📝 Оставить заявку** — переиспользует существующий FSM `CreateRequestSG` с пометкой `Через карточку диллера: <name> (#id)` в комментарии. Лид типа `request`
  - **📞 Заказать звонок** — переиспользует FSM `CallbackSG`, аналогично подставляет пометку. Лид типа `callback`
- `stubs.py` удалён — у Клиента больше нет ни одной заглушки
- В `CallbackSG` добавлена поддержка `comment_prefix` (как уже было в `CreateRequestSG`)

### Итерация 8 — медиа и согласование в Контенте

По уточнению заказчика (ответ #6): в разделе «Контент» маркетинг ведёт посты с медиа и со статусами согласования.

- В `content_items` добавлены поля `file_type`, `telegram_file_id` и `approval_*` (миграция 0008)
- В `ContentStatus` добавлены значения `pending_approval`, `approved`, `rejected` (помимо `draft`/`scheduled`/`published`/`archived`)
- FSM создания записи расширен двумя шагами:
  - **Медиа** — приложить фото/видео/документ/GIF (или «-» чтобы пропустить)
  - **Выбор статуса** — «📝 Черновик» или «📤 На согласование»
- Карточка записи (`📝 Запись #N`) показывает медиа предпросмотром (если есть). Кнопки действий зависят от статуса:
  - `draft` → «📤 На согласование»
  - `pending_approval` → «✅ Одобрить» / «❌ Отклонить»
  - `approved` / `scheduled` → «📢 Опубликовано» / «🗄 В архив»
  - `rejected` → «📤 Повторно на согласование»
- В подменю «📝 Контент» добавлен пункт «🛡 На согласовании» — отдельная очередь pending-записей для модерации (по аналогии с модерацией материалов)
- Согласование доступно любому маркетологу. Эскалация на отдельную роль `head_of_marketing` — точка расширения

### Итерация 7 — Sales «Найти диллера» как рабочий инструмент

По уточнению заказчика (ответ #5): справочник дилеров должен быть не плоским списком, а инструментом маршрутизации.

- В `dealer_profiles` добавлено поле `specialization` (миграция 0007); редактируется из FSM профиля диллера новой кнопкой «✏️ Специализация»
- В `STATUS_LABELS` добавлен `kept_by_sales` («🔒 оставлена у sales»). Это новое значение `RequestStatus`
- Sales: после выбора региона и диллера теперь открывается **карточка диллера** (имя, компания, регион, адрес, телефон, @username, статус, специализация, описание)
- Из карточки три действия:
  - **✅ Передать сюда лид** — подтверждение, реальная передача (status=transferred_to_dealer, assigned_dealer_id=this)
  - **💬 Написать в TG** — URL-кнопка с `https://t.me/<username>` (fallback `tg://user?id=<id>` если username не задан)
  - **🔒 Оставить лид у себя** — `SalesLeadService.keep` переводит лид в `kept_by_sales`. Доступно только владельцу лида (sales, который его взял)
- Пункт меню Sales «📍 Найти диллера» теперь тоже ведёт к карточке диллера (но в режиме без лида — доступно только «💬 Написать в TG»)
- «Запросить согласование у руководителя» из ответа #5 отложено — требует новой роли `sales_lead`/`head_of_sales`

### Итерация 6 — типы лидов, сервисные обращения, согласование контента

По уточнениям заказчика (вопросы #2 и #4 из бизнес-FAQ):

**A. Типы лидов**
- В `client_requests` добавлен `lead_type` (`request`/`consultation`/`callback`)
- У Клиента «Чат с менеджером» → FSM (тема + телефон) создаёт `consultation`-лид
- У Клиента «Заказать звонок» → FSM (телефон + примечание о времени) создаёт `callback`-лид
- В списках лидов у Sales и Дилера тип лида показывается рядом со статусом

**B. Сервисные обращения**
- Новая модель `ServiceRequest` (issue_type: warranty / repair / spare_parts / other, equipment, description, contact_phone, status)
- Клиент «Сервис и запчасти» — FSM из 4 шагов (тип проблемы → модель техники → описание → телефон)
- Дилер «Сервисные обращения» — реальный список: свои + общая очередь без назначенного дилера. Действия: взять в работу / закрыть / отклонить
- Заглушки `Чат с менеджером`, `Заказать звонок`, `Сервис и запчасти` у клиента удалены
- Остался один заглушенный пункт: «Найти диллера» у клиента (использует `DealerDirectoryService`, доделается отдельно)

**C. Локальный контент Дилера на согласование**
- В `sales_materials` добавлены поля `approval_status` (`approved`/`pending`/`rejected`), `approval_note`, `approved_by_user_id`, `approved_at`
- Дилер в подменю «Продающие материалы» теперь видит кнопку «✍️ Загрузить на согласование» (FSM аналогично загрузке у Маркетинга)
- Дилерские загрузки имеют статус `pending`. Маркетинговые сохраняют `approved` сразу (как и было)
- Маркетинг в главном меню получил пункт «🛡 Модерация материалов»: список pending → карточка с медиа → «Одобрить» / «Отклонить»
- Просмотр материалов дилерами теперь фильтрует только `approved`

### Итерация 5 — каталог продукции

- 📦 Новые модели `ProductCategory` и `Product` (название, краткое/полное описание, цена текстом, спецификации, главное фото, sort_order, is_active)
- **Маркетинг/Админ** ведёт каталог: новый пункт меню «📦 Каталог продукции» → создание категории / товара (FSM из 7 шагов: имя → краткое → полное → цена → характеристики → фото)
- **Клиент**: пункты меню «📚 Каталог» и «🔍 Подобрать технику» — реальная логика вместо заглушек. Категории → список товаров с пагинацией → карточка с фото
- Из карточки товара кнопка «📝 Оставить заявку на этот товар» — переходит в существующий FSM создания заявки и подставляет в комментарий пометку `Интересует товар «X» (#id)`
- Slug категории генерируется автоматически из названия (простая транслитерация ру→en)

> По уточнению заказчика: каталог продукции (модели техники) и продающие материалы (PDF/фото/презентации в `sales_materials`) — это разные сущности. Каталог ведётся централизованно Маркетингом/Админом, дилер только использует.

## Структура

```
src/bot/
├── __main__.py                # entry-point
├── config.py                  # pydantic-settings
├── logger.py                  # structlog
├── core/                      # enums, exceptions
├── db/
│   ├── base.py                # DeclarativeBase + TimestampMixin
│   ├── session.py             # engine / sessionmaker
│   ├── models/                # User, ClientProfile, ClientRequest
│   └── repositories/          # CRUD слой
├── cache/
│   ├── redis.py               # фабрика Redis
│   └── role_cache.py          # кэш ролей с TTL
├── schemas/                   # pydantic DTO
├── services/                  # бизнес-логика + n8n клиент
└── api/
    ├── filters.py             # RoleFilter
    ├── texts.py               # тексты ответов
    ├── keyboards/             # клавиатуры
    ├── states/                # FSM группы
    ├── middlewares/           # db, role
    └── handlers/
        ├── start.py
        ├── common.py          # /cancel
        └── client/            # хендлеры роли «Клиент»
```

## Назначение ролей

Новые пользователи автоматически становятся `client`. Сменить роль через SQL:

```sql
UPDATE users SET role = 'dealer'     WHERE telegram_id = 123456789;
UPDATE users SET role = 'sales'      WHERE telegram_id = 123456789;
UPDATE users SET role = 'marketing'  WHERE telegram_id = 123456789;
```

После смены роли инвалидировать кэш Redis (либо подождать `ROLE_CACHE_TTL`):

```bash
redis-cli DEL user:role:123456789
```

## Тестовые данные

### Передать клиентскую заявку дилеру

```sql
-- допустим, диллер имеет users.id = 2
UPDATE client_requests
SET status = 'transferred_to_dealer', assigned_dealer_id = 2
WHERE id = 1;
```

### Добавить продающий материал

Загрузку медиа маркетологом сделаем в итерации «Маркетинг». Сейчас — вставкой `telegram_file_id` напрямую. `file_id` можно получить, отправив боту любой файл и распечатав его в логе либо через сторонний file-id-бот.

```sql
INSERT INTO sales_materials (category, title, description, file_type, telegram_file_id, is_active)
VALUES ('catalogs', 'Каталог 2026', 'Полный каталог моделей', 'document',
        'BQACAgIA...replace_with_real_file_id', true);
```

Категории: `catalogs`, `photos_videos`, `presentations`, `templates`, `training`.
Типы файлов: `document`, `photo`, `video`, `animation`.

## Жизненный цикл лида

```
Клиент создаёт заявку              status = new
        │
        ▼
Sales: Новые лиды → «Взять в работу»     status = in_progress
                                          assigned_sales_id = sales.id
        │
        ▼
Sales: лид → «Передать диллеру» → регион → диллер
                                          status = transferred_to_dealer
                                          assigned_dealer_id = dealer.id
        │
        ▼
Диллер: Новые лиды → «Взять в работу» / «Выполнено» / «Отклонить»
```

## n8n workflow — ожидаемые payload-ы

### `N8N_WEBHOOK_SALES_ASSISTANT`, `N8N_WEBHOOK_EXPO_ASSISTANT`

Бот шлёт:
```json
{"telegram_id": 12345, "question": "...", "context": {"user_id": 1, "role": "sales"}}
```
n8n должен вернуть JSON с одним из ключей: `answer` / `text` / `response` / `result` / `raw`.

### `N8N_WEBHOOK_BROADCAST`

Бот шлёт:
```json
{
  "broadcast_id": 7,
  "text": "Привет! Завтра обновление...",
  "file_type": "photo",
  "telegram_file_id": "AgACAgIA...",
  "target_role": "dealer",
  "recipients": [123, 456, 789]
}
```
n8n итерирует `recipients` и шлёт каждому `sendMessage` / `sendPhoto` / `sendVideo` / `sendDocument` / `sendAnimation` в зависимости от `file_type`.

### `N8N_WEBHOOK_CONTENT_PUBLISH`

Фоновый воркер шлёт по одному запросу на каждую готовую к публикации запись:
```json
{
  "content_id": 42,
  "type": "scheduled",
  "title": "Анонс новой модели",
  "body": "Завтра запуск...",
  "region": "Москва",
  "scheduled_at": "2026-05-13T10:00:00+00:00",
  "file_type": "photo",
  "telegram_file_id": "AgACAgIA..."
}
```
n8n решает, куда публиковать (в каналы дилеров по региону, в соцсети, в VK и т.п.). При HTTP-ошибке запись остаётся в статусе `scheduled`/`approved` — следующий тик повторит.

## Что дальше

- [ ] Тесты aiogram-хендлеров (мок Bot + эмуляция апдейтов)
- [ ] Тесты `content_publisher` через `freezegun` + мок n8n
- [ ] Покрытие edge-кейсов (concurrency на смене статуса лида, race на pending-approval)
```
