from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация приложения
    """

    DATABASE_URL: str

    REDIS_DSN: str

    CBR_URL: str = "https://www.cbr-xml-daily.ru/daily_json.js"

    SESSION_COOKIE: str = "session_id"
    CBR_CACHE_KEY: str = "cbr_usd_rub"
    CBR_TTL_SECONDS: int = 60 * 60  # 1 час

    DELIVERY_RATE_INTERVAL_SECONDS: int = 300  # 5 минут

    APP_NAME: str = "Zhigalev Delivery Club"
    DEBUG: bool = True
    ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Возвращает кэшированный объект настроек."""
    return Settings()


settings = get_settings()
