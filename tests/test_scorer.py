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
