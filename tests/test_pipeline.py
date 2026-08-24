from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.models import DraftPost, SourceItem, StoryCandidate
from app.pipeline import should_send_no_news_status


def make_item(index: int) -> SourceItem:
    return SourceItem(
        source_id="world-athletics",
        source_name="World Athletics",
        title=f"Running story {index}",
        url=f"https://example.com/{index}",
        summary="Diamond League and marathon context",
        published_at=datetime.now(UTC),
        content_hash=f"hash-{index}",
        score=100 - index,
    )


@pytest.mark.asyncio
async def test_run_monitor_skips_existing_drafts_before_applying_limit(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "channel")
    monkeypatch.setenv("TELEGRAM_DRAFT_CHAT_ID", "draft")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "a-secure-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("MAX_DRAFTS_PER_RUN", "2")
    get_settings.cache_clear()

    from app import pipeline

    items = [make_item(index) for index in range(5)]
    existing_urls = {items[0].url, items[1].url}
    drafted_urls: list[str] = []

    monkeypatch.setattr(pipeline, "load_sources", lambda: ([], []))

    async def fake_collect_sources(_sources):
        return items

    async def fake_insert_source_items(_pool, ranked):
        return list(ranked)

    async def fake_draft_exists_for_source(_pool, url):
        return url in existing_urls

    async def fake_get_recent_story_candidates(_pool, _lookback_days):
        return []

    async def fake_write_draft(item, digest_mode=None, related_story=None):
        drafted_urls.append(item.url)
        return DraftPost(
            text=f"Draft for {item.title}",
            source_url=item.url,
            source_title=item.source_name,
        )

    async def fake_insert_draft(_pool, draft):
        draft.id = len(drafted_urls)
        return draft

    class FakeTelegramClient:
        async def send_draft(self, draft):
            return draft.id

    async def fake_mark_draft_message(_pool, _draft_id, _message_id):
        return None

    async def fake_insert_run_log(_pool, _mode, _status, _message):
        return None

    import app.db.repository as repository

    monkeypatch.setattr(pipeline, "collect_sources", fake_collect_sources)
    monkeypatch.setattr(pipeline, "insert_source_items", fake_insert_source_items)
    monkeypatch.setattr(pipeline, "draft_exists_for_source", fake_draft_exists_for_source)
    monkeypatch.setattr(pipeline, "get_recent_story_candidates", fake_get_recent_story_candidates)
    monkeypatch.setattr(pipeline, "write_draft", fake_write_draft)
    monkeypatch.setattr(pipeline, "insert_draft", fake_insert_draft)
    monkeypatch.setattr(pipeline, "insert_run_log", fake_insert_run_log)
    monkeypatch.setattr(repository, "mark_draft_message", fake_mark_draft_message)
    monkeypatch.setattr(pipeline, "TelegramClient", FakeTelegramClient)

    created = await pipeline.run_monitor(pool=object(), mode="morning")

    assert created == 2
    assert drafted_urls == [items[2].url, items[3].url]


@pytest.mark.asyncio
async def test_run_monitor_skips_related_story_without_update(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@channel")
    monkeypatch.setenv("TELEGRAM_DRAFT_CHAT_ID", "draft")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "a-secure-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("MAX_DRAFTS_PER_RUN", "2")
    monkeypatch.setenv("DUPLICATE_STORY_SIMILARITY_THRESHOLD", "0.2")
    get_settings.cache_clear()

    from app import pipeline

    items = [
        SourceItem(
            source_id="marathon",
            source_name="Marathon Handbook",
            title="Comrades Marathon centenary guide for runners",
            url="https://example.com/new",
            summary="Background on the centenary race.",
            published_at=datetime.now(UTC),
            content_hash="hash-new",
            score=150,
        )
    ]
    related = StoryCandidate(
        title="Comrades Marathon centenary guide",
        text="The channel already covered the basic race background.",
        source_url="https://example.com/old",
        status="published",
        published_message_id=10,
    )
    drafted_urls: list[str] = []

    monkeypatch.setattr(pipeline, "load_sources", lambda: ([], []))

    async def fake_collect_sources(_sources):
        return items

    async def fake_insert_source_items(_pool, ranked):
        return list(ranked)

    async def fake_draft_exists_for_source(_pool, _url):
        return False

    async def fake_get_recent_story_candidates(_pool, _lookback_days):
        return [related]

    async def fake_write_draft(item, digest_mode=None, related_story=None):
        drafted_urls.append(item.url)
        return DraftPost(text="Draft", source_url=item.url, source_title=item.source_name)

    async def fake_insert_run_log(_pool, _mode, _status, _message):
        return None

    monkeypatch.setattr(pipeline, "collect_sources", fake_collect_sources)
    monkeypatch.setattr(pipeline, "insert_source_items", fake_insert_source_items)
    monkeypatch.setattr(pipeline, "draft_exists_for_source", fake_draft_exists_for_source)
    monkeypatch.setattr(pipeline, "get_recent_story_candidates", fake_get_recent_story_candidates)
    monkeypatch.setattr(pipeline, "write_draft", fake_write_draft)
    monkeypatch.setattr(pipeline, "insert_run_log", fake_insert_run_log)

    created = await pipeline.run_monitor(pool=object(), mode="morning")

    assert created == 0
    assert drafted_urls == []


@pytest.mark.asyncio
async def test_run_monitor_allows_related_story_with_update(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@beyond_the_1ine")
    monkeypatch.setenv("TELEGRAM_DRAFT_CHAT_ID", "draft")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "a-secure-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("MAX_DRAFTS_PER_RUN", "1")
    monkeypatch.setenv("DUPLICATE_STORY_SIMILARITY_THRESHOLD", "0.2")
    get_settings.cache_clear()

    from app import pipeline

    items = [
        SourceItem(
            source_id="marathon",
            source_name="Marathon Handbook",
            title="Comrades Marathon registration opens Tuesday",
            url="https://example.com/update",
            summary="The centenary race entry ballot schedule is now confirmed.",
            published_at=datetime.now(UTC),
            content_hash="hash-update",
            score=150,
        )
    ]
    related = StoryCandidate(
        title="Comrades Marathon centenary guide",
        text="The channel already covered the basic race background.",
        source_url="https://example.com/old",
        status="published",
        published_message_id=77,
    )
    received_related: list[StoryCandidate | None] = []
    inserted_drafts: list[DraftPost] = []

    monkeypatch.setattr(pipeline, "load_sources", lambda: ([], []))

    async def fake_collect_sources(_sources):
        return items

    async def fake_insert_source_items(_pool, ranked):
        return list(ranked)

    async def fake_draft_exists_for_source(_pool, _url):
        return False

    async def fake_get_recent_story_candidates(_pool, _lookback_days):
        return [related]

    async def fake_write_draft(item, digest_mode=None, related_story=None):
        received_related.append(related_story)
        return DraftPost(text="Draft update", source_url=item.url, source_title=item.source_name)

    async def fake_insert_draft(_pool, draft):
        draft.id = 1
        inserted_drafts.append(draft)
        return draft

    class FakeTelegramClient:
        async def send_draft(self, draft):
            return draft.id

    async def fake_mark_draft_message(_pool, _draft_id, _message_id):
        return None

    async def fake_insert_run_log(_pool, _mode, _status, _message):
        return None

    import app.db.repository as repository

    monkeypatch.setattr(pipeline, "collect_sources", fake_collect_sources)
    monkeypatch.setattr(pipeline, "insert_source_items", fake_insert_source_items)
    monkeypatch.setattr(pipeline, "draft_exists_for_source", fake_draft_exists_for_source)
    monkeypatch.setattr(pipeline, "get_recent_story_candidates", fake_get_recent_story_candidates)
    monkeypatch.setattr(pipeline, "write_draft", fake_write_draft)
    monkeypatch.setattr(pipeline, "insert_draft", fake_insert_draft)
    monkeypatch.setattr(pipeline, "insert_run_log", fake_insert_run_log)
    monkeypatch.setattr(repository, "mark_draft_message", fake_mark_draft_message)
    monkeypatch.setattr(pipeline, "TelegramClient", FakeTelegramClient)

    created = await pipeline.run_monitor(pool=object(), mode="morning")

    assert created == 1
    assert received_related == [related]
    assert "https://t.me/beyond_the_1ine/77" in inserted_drafts[0].text


def test_should_send_no_news_status_every_threshold_runs() -> None:
    assert should_send_no_news_status(0, 4) is False
    assert should_send_no_news_status(3, 4) is False
    assert should_send_no_news_status(4, 4) is True
    assert should_send_no_news_status(5, 4) is False
    assert should_send_no_news_status(8, 4) is True
