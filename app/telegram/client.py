import httpx

from app.core.config import get_settings
from app.models import DraftPost
from app.telegram.formatting import append_source, make_draft_keyboard


class TelegramClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}"

    async def _post(self, method: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}/{method}", json=payload)
            response.raise_for_status()
            data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data

    async def send_draft(self, draft: DraftPost) -> int:
        if draft.id is None:
            raise ValueError("draft.id is required before sending draft")
        text = append_source(draft.text, draft.source_url, draft.source_title)
        data = await self._post(
            "sendMessage",
            {
                "chat_id": self.settings.telegram_draft_chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": draft.disable_web_page_preview,
                "reply_markup": make_draft_keyboard(draft.id),
            },
        )
        return int(data["result"]["message_id"])

    async def publish(self, draft: DraftPost) -> int:
        text = append_source(draft.text, draft.source_url, draft.source_title)
        data = await self._post(
            "sendMessage",
            {
                "chat_id": self.settings.telegram_channel_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": draft.disable_web_page_preview,
            },
        )
        return int(data["result"]["message_id"])

    async def send_draft_status(self, text: str) -> int:
        data = await self._post(
            "sendMessage",
            {
                "chat_id": self.settings.telegram_draft_chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )
        return int(data["result"]["message_id"])

    async def answer_callback(self, callback_query_id: str, text: str) -> None:
        await self._post(
            "answerCallbackQuery",
            {"callback_query_id": callback_query_id, "text": text},
        )
