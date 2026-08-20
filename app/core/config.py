from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    auto_publish: bool = False
    public_base_url: str = ""

    database_url: str = Field(..., min_length=1)

    telegram_bot_token: str = Field(..., min_length=1)
    telegram_channel_id: str = Field(..., min_length=1)
    telegram_draft_chat_id: str = Field(..., min_length=1)
    telegram_webhook_secret: str = Field(..., min_length=16)

    openai_api_key: str = Field(..., min_length=1)
    openai_model: str = "gpt-4.1-mini"

    timezone: str = "Asia/Almaty"
    max_drafts_per_run: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
