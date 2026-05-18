#!/usr/bin/env bash
# Тестовая публикация. Канал, куда уходит сообщение, берётся из $vars.PUBLISH_CHANNEL_ID в n8n.
set -euo pipefail

BASE="${N8N_BASE_URL:-http://localhost:5678}"

curl -sS -X POST "$BASE/webhook/content-publish" \
  -H 'Content-Type: application/json' \
  -d '{
    "content_id": 999,
    "type": "scheduled",
    "title": "Тестовая публикация",
    "body": "Это тестовое сообщение из n8n.",
    "region": null,
    "scheduled_at": null,
    "file_type": null,
    "telegram_file_id": null
  }' \
  | jq .
