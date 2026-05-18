from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", extra="ignore")

    token: SecretStr
    drop_pending_updates: bool = True


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    db: str = "bolshaya_zemlya"
    user: str = "bot"
    password: SecretStr = SecretStr("bot")
    echo: bool = False

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_dsn(self) -> str:
        return (
            f"postgresql+psycopg2://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: SecretStr | None = None

    @property
    def url(self) -> str:
        auth = f":{self.password.get_secret_value()}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    role_cache_ttl: int = Field(default=1800, alias="ROLE_CACHE_TTL")


class N8nSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="N8N_", env_file=".env", extra="ignore")

    base_url: str = "http://localhost:5678"
    webhook_sales_assistant: str = "/webhook/sales-assistant"
    webhook_expo_assistant: str = "/webhook/expo-assistant"
    webhook_broadcast: str = "/webhook/broadcast"
    webhook_content_publish: str = "/webhook/content-publish"
    request_timeout: int = 30


class PublisherSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PUBLISHER_", env_file=".env", extra="ignore")

    enabled: bool = True
    interval_seconds: int = 60


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=".env", extra="ignore")

    level: str = "INFO"
    as_json: bool = Field(default=False, alias="LOG_JSON")


class Settings:
    def __init__(self) -> None:
        self.telegram = TelegramSettings()
        self.postgres = PostgresSettings()
        self.redis = RedisSettings()
        self.cache = CacheSettings()
        self.n8n = N8nSettings()
        self.publisher = PublisherSettings()
        self.logging = LoggingSettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
