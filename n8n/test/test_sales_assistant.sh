#!/usr/bin/env bash
set -euo pipefail

BASE="${N8N_BASE_URL:-http://localhost:5678}"

curl -sS -X POST "$BASE/webhook/sales-assistant" \
  -H 'Content-Type: application/json' \
  -d '{
    "telegram_id": 123456789,
    "question": "Клиент торгуется по цене трактора. Что предложить?",
    "context": {"user_id": 5, "role": "sales"}
  }' \
  | jq .
