# n8n workflows для бота «Большая Земля»

Бот общается с n8n через 4 webhook-а. Все они слушают POST, путь задаётся в `.env`:

| Переменная в `.env`              | Что делает workflow                       |
| -------------------------------- | ----------------------------------------- |
| `N8N_WEBHOOK_SALES_ASSISTANT`    | ИИ-помощник продажника (LLM)              |
| `N8N_WEBHOOK_EXPO_ASSISTANT`     | ИИ-помощник по выставкам (LLM)            |
| `N8N_WEBHOOK_BROADCAST`          | Массовая рассылка в Telegram              |
| `N8N_WEBHOOK_CONTENT_PUBLISH`    | Автопостинг контента в канал              |

В папке [workflows/](workflows/) лежат готовые JSON-файлы — их можно импортировать в n8n через **Workflows → Import from File**.

## Импорт и активация

1. Открыть UI n8n, перейти в **Workflows → Import from File**, выбрать один из четырёх файлов
2. Открыть импортированный workflow и **активировать** его кнопкой Active в правом верхнем углу
3. Зайти на ноду **Webhook** — скопировать «Production URL» — это и есть полный URL, путь после `/webhook/` должен совпадать со значением в `.env`
4. Для нод **Telegram** и **OpenAI** настроить **Credentials** (одноразово, см. ниже)

Если в `.env` бота прописан путь `N8N_WEBHOOK_BROADCAST=/webhook/broadcast`, то в n8n Webhook-нода должна иметь Path = `broadcast` (без слэша) и Method = POST.

## Подготовка credentials

### Telegram Bot API (для `broadcast` и `content_publish`)

В n8n: **Credentials → Add → Telegram API → Access Token = <ваш BOT_TOKEN>**. Назвать `Bolshaya Zemlya Bot`. На Telegram-нодах в workflow выбрать эти credentials в поле Credential.

> Тот же токен, что в `.env` бота — n8n использует его параллельно для рассылок.

### OpenAI / любая LLM (для AI-ассистентов)

В n8n: **Credentials → Add → OpenAI API → API Key = <sk-...>**. Назвать `OpenAI`.

Если используете другую LLM (Anthropic, Yandex GPT, локальная) — замените ноду OpenAI в импортированном workflow на нужную (Anthropic, HTTP Request с вашим эндпоинтом и т.п.) и обновите подключение к Respond-ноде.

### Защита webhook-ов токеном (рекомендуется)

По умолчанию webhook'и n8n **публичные** — любой, кто знает URL, может их дёрнуть. На stage/prod закрой их Header Auth:

1. В каждом импортированном workflow открой ноду **Webhook** → **Authentication: Header Auth** → создай credential «N8N Webhook» со значениями:
   - **Name** = `Authorization`
   - **Value** = `Bearer my-secret-token` (любая строка, лучше длинная случайная)
2. В `.env` бота:
   ```env
   N8N_AUTH_HEADER=Bearer my-secret-token
   ```
3. Бот автоматически будет слать заголовок `Authorization: Bearer my-secret-token` в каждом вызове.

Альтернативно — Basic Auth: на стороне n8n укажи user/pass, в `.env` бота:
```env
N8N_AUTH_HEADER=Basic <base64 от "user:pass">
```

Если `N8N_AUTH_HEADER` пуст — заголовок не отправляется (для локальной разработки это удобно).

### Канал/чат публикации (для `content_publish`)

Выпускающий канал, куда улетают опубликованные записи:

- Добавьте бота админом в нужный Telegram-канал
- Получите `chat_id` канала (через `getUpdates` или сторонним сервисом — обычно отрицательное число типа `-100xxxxxxxxxx`)
- В n8n: **Settings → Variables** (или Environment) → создайте переменную `PUBLISH_CHANNEL_ID` со значением `chat_id`

В workflow `content_publish.json` Telegram-нода использует `={{$vars.PUBLISH_CHANNEL_ID}}`.

## Payload-формат каждого workflow

### sales_assistant / expo_assistant

Входящий POST:
```json
{
  "telegram_id": 12345678,
  "question": "Клиент торгуется по цене трактора XL-200. Что предложить?",
  "context": {"user_id": 5, "role": "sales"}
}
```

Workflow должен вернуть JSON с одним из ключей: `answer` / `text` / `response` / `result`:
```json
{"answer": "Предложите скидку 3% при оплате до конца месяца..."}
```

При недоступности n8n или ошибке HTTP — бот покажет «ИИ-помощник временно недоступен» и не упадёт.

### broadcast

Входящий POST:
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

`file_type` ∈ `null`, `"document"`, `"photo"`, `"video"`, `"animation"`. Если `null` — отправляется только текст.

Workflow итерирует `recipients`, для каждого telegram_id вызывает соответствующий Telegram метод (`sendMessage` / `sendPhoto` / `sendVideo` / `sendDocument` / `sendAnimation`).

Ответ не требуется (бот игнорирует тело, важен только HTTP 2xx).

### content_publish

Входящий POST (по одной записи на тик):
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

Workflow собирает caption (`<b>{title}</b>\n\n{body}`) и отправляет в `PUBLISH_CHANNEL_ID`. При наличии медиа — `sendPhoto`/`sendVideo`/`sendDocument`/`sendAnimation`, без медиа — `sendMessage`.

При HTTP-ошибке от n8n запись останется в статусе `scheduled` — фоновый воркер бота повторит на следующем тике.

## Тестирование без бота

В папке [test/](test/) лежат `curl`-скрипты для ручной проверки каждого webhook-а локально:

```bash
cd n8n/test
N8N_BASE_URL=http://localhost:5678 bash test_sales_assistant.sh
```

## Где смотреть payload, который реально шлёт бот

В n8n-Webhook ноде включить **Logs → Save → Yes**. После любого вызова из бота на ноде появится колонка `executions` — там полный JSON.

В коде бота payload-ы формируются здесь:
- AI-ассистенты: [src/bot/services/sales_assistant_service.py](../src/bot/services/sales_assistant_service.py) и [expo_assistant_service.py](../src/bot/services/expo_assistant_service.py)
- broadcast: [src/bot/services/broadcast_service.py](../src/bot/services/broadcast_service.py)
- content_publish: [src/bot/services/content_publisher.py](../src/bot/services/content_publisher.py)

## Опционально: запуск n8n рядом с ботом

Если n8n ещё не развёрнут, добавьте сервис в `docker-compose.yml`:

```yaml
  n8n:
    image: n8nio/n8n:latest
    container_name: bz_n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      N8N_HOST: localhost
      N8N_PROTOCOL: http
      N8N_PORT: 5678
      WEBHOOK_URL: http://localhost:5678/
      GENERIC_TIMEZONE: UTC
    volumes:
      - ./data/n8n:/home/node/.n8n
```

И в `.env` бота: `N8N_BASE_URL=http://localhost:5678` (если бот тоже в docker-сети — `http://n8n:5678`).
