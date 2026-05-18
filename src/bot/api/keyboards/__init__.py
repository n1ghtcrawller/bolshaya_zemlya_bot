def truncate(value: str, limit: int = 50) -> str:
    """Обрезает текст для inline-кнопки Telegram (визуальный лимит ~30-50 символов)."""
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: max(limit - 1, 1)].rstrip() + "…"
