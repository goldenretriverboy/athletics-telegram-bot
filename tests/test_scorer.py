from app.models import SourceItem
from app.ranking.scorer import rank_items, score_item


def make_item(title: str, summary: str = "", score: int = 10) -> SourceItem:
    return SourceItem(
        source_id="test",
        source_name="Test",
        title=title,
        url=f"https://example.com/{title}",
        summary=summary,
        published_at=None,
        content_hash=title,
        score=score,
    )


def test_score_item_boosts_watch_terms() -> None:
    item = score_item(make_item("Andreas Almgren marathon debut"), ["Andreas Almgren"])
    assert item.score > 10


def test_rank_items_returns_highest_scores_first() -> None:
    items = [make_item("minor update"), make_item("Duplantis world record attempt")]
    ranked = rank_items(items, [], limit=1)
    assert ranked[0].title == "Duplantis world record attempt"


def test_rank_items_can_filter_by_min_score() -> None:
    items = [
        make_item("minor update", score=80),
        make_item("Duplantis world record attempt", score=80),
    ]
    ranked = rank_items(items, [], limit=2, min_score=115)
    assert [item.title for item in ranked] == ["Duplantis world record attempt"]


def test_marathon_record_story_gets_strong_priority() -> None:
    item = score_item(make_item("Berlin Marathon winner breaks course record"), [])

    assert item.score >= 95


def test_sports_science_story_gets_priority_when_relevant_to_running() -> None:
    item = score_item(
        make_item("New study links heat and hydration to marathon performance"),
        [],
    )

    assert item.score >= 75


def test_kazakhstan_event_change_gets_local_priority() -> None:
    item = score_item(make_item("Almaty Marathon cancelled after route change"), [])

    assert item.score >= 95


def test_accessible_regional_major_start_gets_priority() -> None:
    item = score_item(make_item("Beijing Marathon announces elite field"), [])

    assert item.score >= 95
