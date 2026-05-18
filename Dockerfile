FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# pyproject и src нужны вместе для setuptools src-layout: pip install . без src
# не установит сам пакет `bot` — будет ставиться только список зависимостей.
COPY pyproject.toml ./
COPY src ./src
RUN pip install .

# Миграции в отдельном слое — их правки не пересобирают pip install.
COPY alembic ./alembic
COPY alembic.ini ./

# Non-root.
RUN useradd --create-home --uid 1000 bot \
    && chown -R bot:bot /app
USER bot

# Миграции применяются на старте, чтобы бот не упал на отсутствующих таблицах.
CMD ["sh", "-c", "alembic upgrade head && python -m bot"]
