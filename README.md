# Bot «Большая Земля»

Telegram-бот для проекта «Большая Земля» (с/х техника). 6 ролей, 11 моделей данных, 4 интеграции с n8n, фоновый автопостинг, 30 unit/integration-тестов.

## Стек

- **aiogram 3** — Telegram Bot framework, FSM на Redis
- **SQLAlchemy 2 (async) + PostgreSQL/asyncpg** — БД, миграции через alembic
- **Redis** — кэш ролей (TTL 30 мин) + хранилище FSM-состояний
- **pydantic v2 + pydantic-settings** — DTO и конфигурация
- **httpx** — асинхронные вызовы n8n webhook-ов
- **APScheduler** — фоновый воркер автопостинга контента
- **structlog** — структурированное логирование

## Архитектура

Clean Architecture, 5 слоёв сверху вниз:

```
TG API (handlers / keyboards / middlewares)     src/bot/api/
        │
        ▼
Service слой (бизнес-логика, n8n клиент)        src/bot/services/
        │
        ├──► Redis (FSM + кэш ролей)            src/bot/cache/
        ▼
CRUD слой (repositories)                        src/bot/db/repositories/
        │
        ▼
PostgreSQL (модели SQLAlchemy + alembic)        src/bot/db/models/
        │
        └──► n8n (HTTP, 4 webhook-а)            src/bot/services/n8n_client.py
```

## Быстрый старт

```powershell
# 1. Виртуальное окружение и зависимости
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .

# 2. Конфиг
copy .env.example .env
# отредактируйте BOT_TOKEN

# 3. PostgreSQL + Redis локально
docker compose up -d

# 4. Миграции
alembic upgrade head

# 5. Запуск
python -m bot
```

## Роли и функционал

Пользователь получает роль `client` при первом `/start`. Сменить роль — через UI Маркетинга (👥 Пользователи) или SQL (см. ниже).

### 🟢 Клиент

| Пункт меню | Что делает |
|---|---|
| 📚 Каталог | Категории → товары с пагинацией → карточка с фото |
| 🔍 Подобрать технику | Тот же каталог, обёрнутый в подбор |
| 📝 Оставить заявку | FSM (имя → телефон → комментарий → подтверждение). Создаёт лид типа `request` |
| 📍 Найти диллера | Регион → дилер → карточка с действиями: написать в TG / оставить заявку / заказать звонок |
| 🔧 Сервис и запчасти | FSM (тип проблемы → техника → описание → телефон) → ServiceRequest |
| 💬 Чат с менеджером | FSM (тема + телефон) → лид типа `consultation` |
| 📞 Заказать звонок | FSM (телефон + удобное время) → лид типа `callback` |
| 📋 Мои заявки | Список + детали с подсветкой статуса |
| 👤 Профиль | Просмотр |

### 🟠 Диллер

| Пункт меню | Что делает |
|---|---|
| 📥 Новые лиды | Лиды, назначенные на этого дилера. Действия: взять в работу / выполнено / отклонить |
| 📚 Продающие материалы | 5 категорий (каталоги, фото/видео, презентации, шаблоны, обучение). Отдача через `telegram_file_id`. Видны только `approved` материалы |
| ✍️ Загрузить на согласование | FSM (категория → файл → название → описание). Создаёт `pending`-материал, попадает в очередь модерации Маркетинга |
| 🔧 Сервисные обращения | Свои + общая очередь без назначенного дилера. Действия: взять / закрыть / отклонить |
| 📊 Статистика | Счётчики своих лидов по статусам |
| 👤 Профиль | Телефон / компания / регион / адрес / специализация / описание. FSM редактирования по полю |

### 🔵 Sales

| Пункт меню | Что делает |
|---|---|
| 📥 Новые лиды | Общая очередь без `assigned_sales_id`. «Взять в работу» закрепляет лид |
| ⚙️ В работе | Свои лиды `in_progress`. Открыть → передать диллеру / оставить у себя / запросить согласование |
| 📨 Переданы диллеру | Свои переданные лиды (для контроля) |
| 📍 Найти диллера | Регион → список дилеров → **карточка** (контакты, специализация). В режиме передачи лида — кнопки действий |
| 🤖 ИИ-помощник | FSM → `N8nClient.sales_assistant` → ответ LLM. При недоступности n8n — мягкое сообщение |

**Жизненный цикл лида** (с эскалацией):

```
Клиент создаёт заявку
                    status = new
                    ▼
Sales: «Взять в работу»
                    status = in_progress
                    assigned_sales_id = sales.id
                    ▼
Sales → карточка диллера →
   ├─ ✅ Передать                   status = transferred_to_dealer
   ├─ 👔 Запросить согласование     LeadApproval(pending)
   │        │
   │        ▼
   │   HeadOfSales → одобрить       status = transferred_to_dealer
   │              → отклонить       лид остаётся у sales
   │
   └─ 🔒 Оставить у себя            status = kept_by_sales

Диллер: «Новые лиды» → «Взять в работу» → «Выполнено» / «Отклонить»
```

### 👔 HeadOfSales

Расширенный Sales — то же меню + дополнительный пункт **«👔 Очередь согласований»**. Список pending-запросов от Sales-менеджеров → карточка с деталями → одобрить (реальная передача лида) или отклонить.

Кнопка «👔 Запросить согласование» в карточке диллера у Sales появляется только если в БД есть хотя бы один пользователь с этой ролью.

### 🟣 Маркетинг / Админ

| Пункт меню | Что делает |
|---|---|
| 📊 Дашборд | Подменю: 📋 Сводка (users by role, leads by status), 📍 По диллерам (топ-10 с разбивкой по статусам), 📦 По продуктам (топ-10 с категорией) |
| 👥 Пользователи | Список по ролям → карточка → смена роли (с инвалидацией Redis-кэша) |
| 📚 Материалы (загрузка) | FSM: категория → файл → название → описание. Сохраняется сразу как `approved` |
| 📣 Рассылки | FSM: текст → медиа → сегмент (по роли или «все») → подтверждение → отправка через `N8nClient.broadcast`. История доступна из меню |
| 📝 Контент | 4 типа записей (план / идея / региональная / отложка). FSM: title → body → region → дата → медиа → выбор статуса (draft / на согласование). В карточке — действия по статусу |
| 🎪 Выставки | Ближайшие, карточка, создание (название/локация/даты/продукты/описание) |
| 📦 Каталог продукции | Создание категорий и товаров (FSM из 7 шагов с фото) |
| 🛡 Модерация материалов | Очередь дилерских материалов в статусе `pending` → одобрить / отклонить |
| 🤖 ИИ-помощник (Выставки) | `N8nClient.expo_assistant`, такой же паттерн как у Sales |

В подменю Контента есть отдельная очередь «🛡 На согласовании» с действиями одобрить/отклонить для записей в `pending_approval`.

### 🟣 HeadOfMarketing

Та же роль и то же меню, что у Маркетинга. Отличие — **только** этот пользователь может одобрять / отклонять контент и материалы. Если HeadOfMarketing в БД ещё не назначен — fallback: одобрять может любой маркетолог, чтобы очередь не зависала ([approval_policy.py](src/bot/services/approval_policy.py)).

## База данных

11 моделей (10 миграций):

| Модель | Назначение |
|---|---|
| `users` | Все пользователи бота с ролью |
| `client_profiles` | Профиль клиента (телефон, регион, компания, email) |
| `client_requests` | Лиды: `lead_type` (request / consultation / callback), `status`, FK на sales / dealer / product |
| `dealer_profiles` | Профиль дилера (телефон, компания, регион, адрес, специализация, описание) |
| `service_requests` | Сервисные обращения клиентов (гарантия / ремонт / запчасти / другое) |
| `lead_approvals` | Запросы Sales → HeadOfSales на согласование передачи лида |
| `sales_materials` | Продающие материалы (Telegram `file_id`, категория, `approval_status`) |
| `product_categories` | Категории каталога продукции |
| `products` | Товары каталога (название, описание, цена текстом, фото) |
| `content_items` | Контент-записи Маркетинга (4 типа, медиа, статусы согласования) |
| `broadcasts` | История рассылок (текст, медиа, сегмент, sent_count, error) |
| `expos` | Выставки (название, локация, даты, продукты, описание) |

Миграции в [alembic/versions/](alembic/versions/) — последовательно применяются `alembic upgrade head`.

## Назначение ролей

При смене роли в БД нужно инвалидировать Redis-кэш (либо подождать `ROLE_CACHE_TTL`):

```sql
UPDATE users SET role = 'dealer'             WHERE telegram_id = 123456789;
UPDATE users SET role = 'sales'              WHERE telegram_id = 123456789;
UPDATE users SET role = 'head_of_sales'      WHERE telegram_id = 123456789;
UPDATE users SET role = 'marketing'          WHERE telegram_id = 123456789;
UPDATE users SET role = 'head_of_marketing'  WHERE telegram_id = 123456789;
```

```bash
redis-cli DEL user:role:123456789
```

В UI Маркетинга («👥 Пользователи») смена роли инвалидирует кэш автоматически.

## n8n: 4 интеграции

| Переменная в `.env` | Что делает workflow |
|---|---|
| `N8N_WEBHOOK_SALES_ASSISTANT` | LLM-помощник Sales (вопрос → ответ) |
| `N8N_WEBHOOK_EXPO_ASSISTANT`  | LLM-помощник по выставкам |
| `N8N_WEBHOOK_BROADCAST`       | Массовая рассылка по списку `recipients` |
| `N8N_WEBHOOK_CONTENT_PUBLISH` | Автопостинг контент-записи в канал |

В папке [n8n/](n8n/) лежат **готовые JSON-файлы** для импорта в n8n + подробная [n8n/README.md](n8n/README.md) с настройкой credentials. В [n8n/test/](n8n/test/) — curl-скрипты для ручной проверки webhook-ов.

При недоступности n8n: AI-ассистенты показывают «временно недоступен» (не падают). Рассылки помечаются `failed`. Автопостинг повторяет на следующем тике.

## Автопостинг контента (cron)

`APScheduler` внутри bot-процесса каждые `PUBLISHER_INTERVAL_SECONDS` (60 по умолчанию) обходит `content_items` со `status in (scheduled, approved)` и `scheduled_at <= now` UTC, отдаёт каждую запись в `N8N_WEBHOOK_CONTENT_PUBLISH`. При успехе ставит `status = published`.

Защита: `max_instances=1, coalesce=True` — параллельные тики не запускаются. Отключение: `PUBLISHER_ENABLED=false`. Подробнее — в [src/bot/services/content_publisher.py](src/bot/services/content_publisher.py).

## Тесты

30 тестов на критичную бизнес-логику, выполняются за ~1 сек на in-memory SQLite (aiosqlite).

```powershell
pip install -e ".[dev]"
pytest -q
```

```
tests/
├── conftest.py                              # фикстуры engine/session, фабрика make_user
├── unit/
│   ├── test_catalog_admin_service.py        # slugify, уникальность slug
│   ├── test_approval_policy.py              # fallback head_of_marketing → marketer
│   ├── test_content_service.py              # выбор статуса при create
│   └── test_sales_lead_service.py           # take / transfer / keep / reject с проверкой доступа
└── integration/
    ├── test_lead_approval_flow.py           # request → approve → реальная передача
    ├── test_client_request_repository.py
    ├── test_sales_material_repository.py
    ├── test_dealer_directory_repository.py
    └── test_dashboard_service.py            # snapshot / dealers_breakdown / top_products
```

## Структура проекта

```
bot_bolshaya_zemlya/
├── alembic.ini
├── docker-compose.yml          # postgres + redis
├── pyproject.toml
├── .env.example
├── alembic/
│   ├── env.py
│   └── versions/               # 10 миграций (0001 → 0010)
├── src/bot/
│   ├── __main__.py             # entry-point: bot + scheduler
│   ├── config.py               # pydantic-settings (Telegram/Postgres/Redis/N8n/Publisher/Logging)
│   ├── logger.py               # structlog
│   ├── core/
│   │   ├── enums.py            # UserRole, RequestStatus, LeadType, ContentStatus, ApprovalStatus, ...
│   │   └── exceptions.py
│   ├── db/
│   │   ├── base.py             # DeclarativeBase + TimestampMixin
│   │   ├── session.py          # async engine / sessionmaker
│   │   ├── models/             # 11 моделей
│   │   └── repositories/       # 12 CRUD-классов
│   ├── cache/
│   │   ├── redis.py            # фабрика Redis (shared для RedisStorage и RoleCache)
│   │   └── role_cache.py       # кэш роли по telegram_id с TTL
│   ├── schemas/                # pydantic DTO (user, client, dealer, request, marketing)
│   ├── services/               # бизнес-логика (15+ сервисов) + n8n_client + content_publisher
│   └── api/
│       ├── filters.py          # RoleFilter (поддерживает несколько ролей)
│       ├── texts.py            # все тексты в одном файле
│       ├── keyboards/          # client / dealer / sales / marketing / catalog
│       ├── states/             # FSM-группы по ролям
│       ├── middlewares/        # db (session injection) / role (определение роли + автосоздание)
│       └── handlers/
│           ├── start.py        # /start с маршрутизацией по роли
│           ├── common.py       # /cancel
│           ├── client/         # 9 модулей
│           ├── dealer/         # 7 модулей
│           ├── sales/          # 6 модулей (включая hos_queue для HeadOfSales)
│           └── marketing/      # 10 модулей
├── n8n/                        # workflow для n8n
│   ├── README.md
│   ├── workflows/              # 4 JSON-файла для импорта
│   └── test/                   # curl-скрипты
└── tests/                      # pytest
```

## Конфигурация (.env)

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram-бота | — |
| `BOT_DROP_PENDING_UPDATES` | Сбрасывать накопившиеся апдейты при старте | `true` |
| `POSTGRES_*` | Креды БД | bot/bot/localhost:5432 |
| `REDIS_*` | Подключение к Redis | localhost:6379 |
| `ROLE_CACHE_TTL` | TTL кэша роли в секундах | `1800` |
| `N8N_BASE_URL` | Базовый URL n8n | `http://localhost:5678` |
| `N8N_WEBHOOK_*` | Пути четырёх webhook-ов | см. `.env.example` |
| `N8N_REQUEST_TIMEOUT` | Таймаут httpx на вызовы n8n | `30` |
| `PUBLISHER_ENABLED` | Включить автопостинг | `true` |
| `PUBLISHER_INTERVAL_SECONDS` | Период тиков воркера | `60` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` |
| `LOG_JSON` | JSON-логи (structlog JSONRenderer) | `false` |

## Полезные SQL-сниппеты

**Передать клиентскую заявку дилеру (для теста):**
```sql
UPDATE client_requests
SET status = 'transferred_to_dealer', assigned_dealer_id = 2
WHERE id = 1;
```

**Добавить продающий материал напрямую (минуя UI):**
```sql
INSERT INTO sales_materials
    (category, title, description, file_type, telegram_file_id, is_active, approval_status)
VALUES
    ('catalogs', 'Каталог 2026', 'Полный каталог моделей', 'document',
     'BQACAgIA...replace_with_real_file_id', true, 'approved');
```

Категории: `catalogs`, `photos_videos`, `presentations`, `templates`, `training`.
Типы файлов: `document`, `photo`, `video`, `animation`.

## Что дальше

- [ ] Тесты aiogram-хендлеров (мок Bot + эмуляция апдейтов)
- [ ] Тесты `content_publisher` через `freezegun` + мок n8n
- [ ] Покрытие edge-кейсов (concurrency на смене статуса лида, race на pending-approval)
- [ ] CI (GitHub Actions: ruff + pytest)
