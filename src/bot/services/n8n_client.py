from typing import Any

import httpx

from bot.config import N8nSettings
from bot.core.exceptions import N8nUnavailableError
from bot.logger import get_logger

log = get_logger(__name__)


class N8nClient:
    """Тонкая обёртка над httpx для вызова n8n webhook-ов.

    Эндпоинты задаются в .env как пути; реальные workflow подключим позже.
    """

    def __init__(self, settings: N8nSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    def _url(self, path: str) -> str:
        return f"{self._settings.base_url.rstrip('/')}/{path.lstrip('/')}"

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._url(path)
        try:
            resp = await self._client.post(
                url, json=payload, timeout=self._settings.request_timeout
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("n8n_request_failed", url=url, error=str(exc))
            raise N8nUnavailableError(str(exc)) from exc

        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}

    async def sales_assistant(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post(self._settings.webhook_sales_assistant, payload)

    async def expo_assistant(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post(self._settings.webhook_expo_assistant, payload)

    async def broadcast(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post(self._settings.webhook_broadcast, payload)
