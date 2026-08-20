from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import get_settings
from app.db.pool import create_pool
from app.db.repository import (
    get_draft,
    insert_published_post,
    mark_draft_status,
)
from app.telegram.client import TelegramClient

router = APIRouter()


@router.post("/api/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    settings = get_settings()
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    update = await request.json()
    callback = update.get("callback_query")
    if not callback:
        return {"ok": True, "ignored": True}

    data = callback.get("data", "")
    callback_id = callback["id"]
    action, _, raw_draft_id = data.partition(":")
    if action not in {"publish", "reject", "rewrite"} or not raw_draft_id.isdigit():
        return {"ok": True, "ignored": True}

    draft_id = int(raw_draft_id)
    pool = await create_pool()
    telegram = TelegramClient()
    try:
        draft = await get_draft(pool, draft_id)
        if draft is None:
            await telegram.answer_callback(callback_id, "Черновик не найден")
            return {"ok": False, "error": "draft_not_found"}

        if action == "publish":
            message_id = await telegram.publish(draft)
            await insert_published_post(pool, draft, message_id)
            await mark_draft_status(pool, draft_id, "published")
            await telegram.answer_callback(callback_id, "Опубликовано")
        elif action == "reject":
            await mark_draft_status(pool, draft_id, "rejected")
            await telegram.answer_callback(callback_id, "Отклонено")
        else:
            await mark_draft_status(pool, draft_id, "rewrite_requested")
            await telegram.answer_callback(callback_id, "Поставлено на переписывание")
    finally:
        await pool.close()

    return {"ok": True}
