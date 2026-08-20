import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.web.admin import verify_admin_secret


def test_verify_admin_secret_accepts_webhook_secret(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "channel")
    monkeypatch.setenv("TELEGRAM_DRAFT_CHAT_ID", "draft")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "a-secure-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    get_settings.cache_clear()

    verify_admin_secret("a-secure-secret-value")


def test_verify_admin_secret_rejects_wrong_secret(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "channel")
    monkeypatch.setenv("TELEGRAM_DRAFT_CHAT_ID", "draft")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "a-secure-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc:
        verify_admin_secret("wrong-secret")

    assert exc.value.status_code == 401
