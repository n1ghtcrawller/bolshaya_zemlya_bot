from bot.core.exceptions import N8nUnavailableError
from bot.services.n8n_client import N8nClient


class ExpoAssistantService:
    """Тонкая обёртка над n8n expo_assistant webhook."""

    def __init__(self, n8n: N8nClient) -> None:
        self._n8n = n8n

    async def ask(self, *, telegram_id: int, question: str, context: dict | None = None) -> str:
        payload: dict = {"telegram_id": telegram_id, "question": question}
        if context:
            payload["context"] = context
        try:
            data = await self._n8n.expo_assistant(payload)
        except N8nUnavailableError:
            raise
        for key in ("answer", "text", "response", "result"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
        raw = data.get("raw")
        if isinstance(raw, str) and raw.strip():
            return raw
        return "Пустой ответ от ИИ-помощника."
