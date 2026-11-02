from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkllBridge AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    database_url: str = ""

    db_pool_min_size: int = 1
    db_pool_max_size: int = 10

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
print("Loaded DATABASE_URL:", repr(settings.database_url))
