from typing import Any

import httpx

from bot.config import BitrixSettings
from bot.core.exceptions import BitrixUnavailableError
from bot.logger import get_logger

log = get_logger(__name__)


class BitrixClient:
    """Тонкая обёртка над httpx для вызова входящего вебхука Bitrix24 REST.

    Базовый URL (`webhook_url`) — это путь до кода вебхука, напр.
    https://portal.bitrix24.ru/rest/1/<code>/ ; клиент дописывает имя метода.
    """

    def __init__(self, settings: BitrixSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    def _method_url(self, method: str) -> str:
        if self._settings.webhook_url is None:
            raise BitrixUnavailableError("BITRIX_WEBHOOK_URL is not configured")
        base = self._settings.webhook_url.get_secret_value().rstrip("/")
        return f"{base}/{method}.json"

    async def _call(self, method: str, payload: dict[str, Any]) -> Any:
        url = self._method_url(method)
        try:
            resp = await self._client.post(
                url, json=payload, timeout=self._settings.request_timeout
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            log.warning("bitrix_request_failed", method=method, error=str(exc))
            raise BitrixUnavailableError(str(exc)) from exc
        except ValueError as exc:  # невалидный JSON в ответе
            log.warning("bitrix_bad_response", method=method, error=str(exc))
            raise BitrixUnavailableError(f"invalid JSON response: {exc}") from exc

        if isinstance(data, dict) and data.get("error"):
            description = data.get("error_description") or data["error"]
            log.warning("bitrix_api_error", method=method, error=description)
            raise BitrixUnavailableError(str(description))
        return data.get("result") if isinstance(data, dict) else data

    async def create_lead(self, fields: dict[str, Any]) -> int:
        result = await self._call(
            "crm.lead.add",
            {"fields": fields, "params": {"REGISTER_SONET_EVENT": "Y"}},
        )
        return int(result)
