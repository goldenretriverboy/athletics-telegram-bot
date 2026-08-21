from __future__ import annotations

from pathlib import Path

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.models import DraftPost, SourceItem

STRONG_DRAFT_MODES = {"morning", "analysis", "explainer"}


def load_editorial_rules(path: str = "config/editorial.md") -> str:
    return Path(path).read_text(encoding="utf-8")


def select_draft_model(settings: Settings, digest_mode: str | None) -> str:
    if digest_mode in STRONG_DRAFT_MODES:
        return settings.openai_strong_model
    return settings.openai_hourly_model or settings.openai_model


async def write_draft(item: SourceItem, digest_mode: str | None = None) -> DraftPost:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    editorial_rules = load_editorial_rules()
    mode = digest_mode or "hourly update"
    model = select_draft_model(settings, digest_mode)
    prompt = f"""
Write one Russian Telegram post for an athletics channel.

Mode: {mode}

Editorial rules:
{editorial_rules}

Use only these source-backed facts:
Source title: {item.source_name}
News title: {item.title}
Summary: {item.summary}
URL: {item.url}

Return only the post text. Do not invent facts. Do not include markdown.
Do not include a source line, raw URL, or "Источник:" in the text.
The system appends the source link automatically.
"""
    response = await client.responses.create(
        model=model,
        input=prompt,
    )
    text = response.output_text.strip()
    return DraftPost(
        source_item_id=item.id,
        text=text,
        source_url=item.url,
        source_title=item.source_name,
        disable_web_page_preview=False,
    )
