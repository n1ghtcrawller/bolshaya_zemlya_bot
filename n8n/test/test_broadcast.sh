#!/usr/bin/env bash
# Тестовая рассылка. Подставьте свой Telegram ID в "recipients" — бот должен быть с вами в личке.
set -euo pipefail

BASE="${N8N_BASE_URL:-http://localhost:5678}"
TG_ID="${TG_ID:?Установите TG_ID=<ваш telegram id>}"

curl -sS -X POST "$BASE/webhook/broadcast" \
  -H 'Content-Type: application/json' \
  -d "$(cat <<EOF
{
  "broadcast_id": 999,
  "text": "Тестовая рассылка из n8n. Время: $(date -Iseconds)",
  "file_type": null,
  "telegram_file_id": null,
  "target_role": null,
  "recipients": [${TG_ID}]
}
EOF
)" -i
