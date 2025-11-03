from pydantic_settings import BaseSettings, SettingsConfigDict


class MainSettings(BaseSettings):
    """
    Конфигурация приложения
    """

    DEBUG: bool = False

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_URL: str

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = None
    REDIS_DB: int = 0

    ENV: str = "development"

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


def get_settings() -> MainSettings:
    return MainSettings()


settings = get_settings()
