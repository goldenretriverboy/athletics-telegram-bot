from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

import httpx
from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.models import DraftPost, SourceItem, StoryCandidate

STRONG_DRAFT_MODES = {"morning", "analysis", "explainer"}
MAX_ARTICLE_CONTEXT_CHARS = 12000
SOURCE_LINE_RE = re.compile(r"^\s*(источник|source)\s*:", re.IGNORECASE)
RAW_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


class ReadableHTMLParser(HTMLParser):
    readable_tags = {"article", "main", "p", "li", "h1", "h2", "h3", "blockquote"}
    ignored_tags = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self._readable_depth = 0
        self._ignored_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.ignored_tags:
            self._ignored_depth += 1
            return
        if tag in self.readable_tags:
            self._readable_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if tag in self.readable_tags and self._readable_depth:
            self._readable_depth -= 1
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth or not self._readable_depth:
            return
        text = " ".join(data.split())
        if text:
            self._parts.append(text)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self._parts).splitlines()]
        return "\n".join(line for line in lines if line)


def load_editorial_rules(path: str = "config/editorial.md") -> str:
    return Path(path).read_text(encoding="utf-8")


def select_draft_model(settings: Settings, digest_mode: str | None) -> str:
    if digest_mode in STRONG_DRAFT_MODES:
        return settings.openai_strong_model
    return settings.openai_hourly_model or settings.openai_model


def extract_readable_text(html: str, max_chars: int = MAX_ARTICLE_CONTEXT_CHARS) -> str:
    parser = ReadableHTMLParser()
    parser.feed(html)
    return parser.text()[:max_chars].strip()


async def fetch_article_context(url: str) -> str:
    headers = {"User-Agent": "BeyondTheLineBot/1.0 (+https://t.me/beyond_the_1ine)"}
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        return ""
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        return ""
    return extract_readable_text(response.text)


def build_draft_prompt(
    item: SourceItem,
    editorial_rules: str,
    mode: str,
    article_context: str = "",
    related_story: StoryCandidate | None = None,
) -> str:
    article_section = (
        article_context or "Article text was not available. Use the title and summary only."
    )
    related_section = ""
    if related_story is not None:
        related_section = f"""
This appears to be an update to a story already covered by the channel.
Previous story title: {related_story.title}
Previous post text:
{related_story.text}

Write the new post as an update: make clear what changed now, avoid repeating the old
post, and keep only the old context that helps readers understand the update.
"""
    return f"""
Write one Russian Telegram post for an athletics channel.

Mode: {mode}

Editorial rules:
{editorial_rules}

Use only these source-backed facts:
Source title: {item.source_name}
News title: {item.title}
Summary: {item.summary}
Article text excerpt:
{article_section}
URL: {item.url}
{related_section}

Use the article text excerpt for results, research details, dates, comparisons,
and limitations when it is available.
When web search is available, use it to verify the source URL and find missing official
results, research details, dates, comparisons, or athlete context before writing.
Prefer the original source, official results pages, event organizers, federations, and
reliable specialist athletics outlets.
Before writing, internally extract the strongest source-backed facts from the article excerpt.
If the article text is not available or does not contain a detail, do not invent it.

Return only the post text. Do not invent facts. Do not include markdown.
Never include a source line, raw URL, "Источник:", or "Source:" in the text.
The system appends the source link automatically.
"""


def build_response_params(model: str, prompt: str, web_search_enabled: bool) -> dict[str, object]:
    params: dict[str, object] = {
        "model": model,
        "input": prompt,
    }
    if web_search_enabled:
        params["tools"] = [{"type": "web_search"}]
    return params


def sanitize_generated_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        if SOURCE_LINE_RE.match(line) or RAW_URL_RE.search(line):
            continue
        cleaned_lines.append(line.rstrip())
    cleaned = "\n".join(cleaned_lines).strip()
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")
    return cleaned


async def write_draft(
    item: SourceItem,
    digest_mode: str | None = None,
    related_story: StoryCandidate | None = None,
) -> DraftPost:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    editorial_rules = load_editorial_rules()
    mode = digest_mode or "hourly update"
    model = select_draft_model(settings, digest_mode)
    article_context = await fetch_article_context(item.url)
    prompt = build_draft_prompt(item, editorial_rules, mode, article_context, related_story)
    response_params = build_response_params(model, prompt, settings.openai_web_search_enabled)
    response = await client.responses.create(**response_params)
    text = sanitize_generated_text(response.output_text)
    return DraftPost(
        source_item_id=item.id,
        text=text,
        source_url=item.url,
        source_title=item.source_name,
        disable_web_page_preview=False,
    )
