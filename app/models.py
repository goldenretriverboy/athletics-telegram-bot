from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SourceConfig:
    id: str
    name: str
    type: str
    url: str
    priority: int


@dataclass
class SourceItem:
    source_id: str
    source_name: str
    title: str
    url: str
    summary: str
    published_at: datetime | None
    content_hash: str
    score: int = 0
    id: int | None = None


@dataclass
class DraftPost:
    text: str
    source_url: str
    source_title: str
    source_item_id: int | None = None
    disable_web_page_preview: bool = False
    id: int | None = None


@dataclass
class StoryCandidate:
    title: str
    text: str
    source_url: str
    status: str
    published_message_id: int | None = None
