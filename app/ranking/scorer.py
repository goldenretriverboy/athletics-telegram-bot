from app.models import SourceItem

IMPORTANT_TERMS = {
    "world record": 40,
    "record": 20,
    "diamond league": 20,
    "world marathon majors": 25,
    "marathon": 20,
    "new york": 15,
    "duplantis": 25,
    "almgren": 25,
    "ingebrigtsen": 25,
    "tebogo": 25,
    "kazakhstan": 20,
}


def score_item(item: SourceItem, watch_terms: list[str]) -> SourceItem:
    haystack = f"{item.title} {item.summary}".lower()
    score = item.score
    for term, value in IMPORTANT_TERMS.items():
        if term in haystack:
            score += value
    for term in watch_terms:
        if term.lower() in haystack:
            score += 15
    item.score = score
    return item


def rank_items(items: list[SourceItem], watch_terms: list[str], limit: int) -> list[SourceItem]:
    scored = [score_item(item, watch_terms) for item in items]
    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

