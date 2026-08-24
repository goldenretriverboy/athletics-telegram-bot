from hmac import compare_digest

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.pool import create_pool
from app.db.repository import insert_draft, mark_draft_message
from app.models import DraftPost
from app.pipeline import run_monitor
from app.telegram.client import TelegramClient

router = APIRouter(prefix="/admin", tags=["admin"])


class ManualDraftRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    source_title: str = Field(..., min_length=1)
    disable_web_page_preview: bool = False


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


@router.post("/manual-draft")
async def create_manual_draft(
    payload: ManualDraftRequest,
    x_admin_secret: str | None = Header(default=None),
) -> dict:
    verify_admin_secret(x_admin_secret)
    pool = await create_pool()
    try:
        draft = DraftPost(
            text=payload.text,
            source_url=payload.source_url,
            source_title=payload.source_title,
            disable_web_page_preview=payload.disable_web_page_preview,
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
    if period != "morning":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only morning digest is enabled",
        )
    pool = await create_pool()
    try:
        created = await run_monitor(pool, mode=period)
    finally:
        await pool.close()
    return {"ok": True, "period": period, "created": created}
