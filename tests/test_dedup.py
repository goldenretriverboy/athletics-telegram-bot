from datetime import UTC, datetime

from app.dedup import find_related_story, is_meaningful_update, telegram_post_url
from app.models import SourceItem, StoryCandidate


def make_item(title: str, summary: str = "") -> SourceItem:
    return SourceItem(
        source_id="source",
        source_name="Source",
        title=title,
        url=f"https://example.com/{abs(hash(title))}",
        summary=summary,
        published_at=datetime.now(UTC),
        content_hash=f"hash-{abs(hash(title))}",
    )


def test_find_related_story_matches_same_topic_from_different_url() -> None:
    item = make_item(
        "Comrades Marathon centenary field goes to ballot",
        "The race increased the field to 28,000 runners.",
    )
    candidate = StoryCandidate(
        title="Comrades Marathon centenary entries and ballot",
        text="Organizers changed entry rules for the 100th Comrades Marathon.",
        source_url="https://example.com/old",
        status="published",
    )

    assert find_related_story(item, [candidate], threshold=0.25) == candidate


def test_is_meaningful_update_requires_clear_update_terms() -> None:
    assert is_meaningful_update(make_item("Comrades Marathon guide for runners")) is False
    assert is_meaningful_update(make_item("Comrades Marathon registration opens Tuesday")) is True


def test_telegram_post_url_only_for_public_channel() -> None:
    assert telegram_post_url("@beyond_the_1ine", 42) == "https://t.me/beyond_the_1ine/42"
    assert telegram_post_url("-100123", 42) is None
