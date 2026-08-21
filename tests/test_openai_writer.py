from app.core.config import Settings
from app.writer.openai_writer import select_draft_model


def make_settings() -> Settings:
    return Settings(
        database_url="postgresql://example",
        telegram_bot_token="token",
        telegram_channel_id="channel",
        telegram_draft_chat_id="draft",
        telegram_webhook_secret="a-secure-secret-value",
        openai_api_key="key",
        openai_model="gpt-5-mini",
        openai_hourly_model="gpt-5-mini",
        openai_strong_model="gpt-5.1",
    )


def test_select_draft_model_uses_hourly_model_for_hourly_posts() -> None:
    assert select_draft_model(make_settings(), "hourly") == "gpt-5-mini"


def test_select_draft_model_uses_strong_model_for_morning_digest() -> None:
    assert select_draft_model(make_settings(), "morning") == "gpt-5.1"


def test_select_draft_model_uses_strong_model_for_analysis() -> None:
    assert select_draft_model(make_settings(), "analysis") == "gpt-5.1"
