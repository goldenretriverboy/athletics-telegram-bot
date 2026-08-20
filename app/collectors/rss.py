from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from app.core.hashing import stable_hash
from app.models import SourceConfig, SourceItem


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


async def collect_rss_source(source: SourceConfig) -> list[SourceItem]:
    feed = feedparser.parse(source.url)
    items: list[SourceItem] = []
    for entry in feed.entries[:20]:
        title = str(entry.get("title", "")).strip()
        url = str(entry.get("link", "")).strip()
        if not title or not url:
            continue
        summary = str(entry.get("summary", "")).strip()
        published_at = _parse_date(entry.get("published") or entry.get("updated"))
        items.append(
            SourceItem(
                source_id=source.id,
                source_name=source.name,
                title=title,
                url=url,
                summary=summary,
                published_at=published_at,
                content_hash=stable_hash(f"{title} {url}"),
                score=source.priority,
            )
        )
    return items


async def collect_sources(sources: list[SourceConfig]) -> list[SourceItem]:
    collected: list[SourceItem] = []
    for source in sources:
        if source.type == "rss":
            collected.extend(await collect_rss_source(source))
    return collected
