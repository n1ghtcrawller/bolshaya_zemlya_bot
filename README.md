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

## Что дальше

- [ ] Раздел Клиента **Сервис и запчасти** (FSM создания обращения) + парный список сервисных обращений у Диллера
- [ ] Использовать `DealerDirectoryService` в клиентском пункте «Найти диллера» (сейчас заглушка)
- [ ] Расписания публикаций (cron-задача обходит `content_items` со статусом `scheduled` и публикует через n8n)
- [ ] Аналитика по дилерам / продуктам в дашборде
- [ ] Подключение реальных n8n workflow (заполнить пути в `.env`)
- [ ] Тесты (pytest + pytest-asyncio)
```
