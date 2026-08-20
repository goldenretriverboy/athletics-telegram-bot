from hmac import compare_digest

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import get_settings
from app.db.pool import create_pool
from app.db.repository import insert_draft, mark_draft_message
from app.models import DraftPost
from app.pipeline import run_monitor
from app.telegram.client import TelegramClient

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_secret(secret: str | None) -> None:
    settings = get_settings()
    if not secret or not compare_digest(secret, settings.telegram_webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin secret",
        )


@router.post("/test-draft")
async def create_test_draft(x_admin_secret: str | None = Header(default=None)) -> dict:
    verify_admin_secret(x_admin_secret)
    pool = await create_pool()
    try:
        draft = DraftPost(
            text=(
                "Тестовый черновик: проверяем, что Railway, Postgres и Telegram-бот "
                "связаны правильно. Это сообщение должно остаться только в тестовом "
                "канале BTL Drafts."
            ),
            source_url="https://worldathletics.org/",
            source_title="World Athletics",
            disable_web_page_preview=True,
        )
        draft = await insert_draft(pool, draft)
        message_id = await TelegramClient().send_draft(draft)
        await mark_draft_message(pool, draft.id, message_id)
    finally:
        await pool.close()
    return {"ok": True, "draft_id": draft.id, "message_id": message_id}


@router.post("/run/hourly")
async def run_hourly(x_admin_secret: str | None = Header(default=None)) -> dict:
    verify_admin_secret(x_admin_secret)
    pool = await create_pool()
    try:
        created = await run_monitor(pool, mode="hourly")
    finally:
        await pool.close()
    return {"ok": True, "created": created}


@router.post("/run/digest/{period}")
async def run_digest(period: str, x_admin_secret: str | None = Header(default=None)) -> dict:
    verify_admin_secret(x_admin_secret)
    if period not in {"morning", "evening"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be morning or evening",
        )
    pool = await create_pool()
    try:
        created = await run_monitor(pool, mode=period)
    finally:
        await pool.close()
    return {"ok": True, "period": period, "created": created}
