from __future__ import annotations

import re

from app.models import SourceItem, StoryCandidate

TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)

STOP_WORDS = {
    "about",
    "after",
    "again",
    "and",
    "announces",
    "for",
    "from",
    "into",
    "new",
    "news",
    "of",
    "on",
    "the",
    "this",
    "to",
    "with",
    "для",
    "его",
    "еще",
    "как",
    "или",
    "над",
    "новости",
    "новый",
    "про",
    "при",
    "что",
    "это",
}

UPDATE_TERMS = {
    "approved",
    "ballot",
    "cancelled",
    "canceled",
    "course",
    "deadline",
    "draw",
    "entries",
    "entry",
    "field",
    "final",
    "injury",
    "joins",
    "opens",
    "postponed",
    "prize",
    "record",
    "registration",
    "result",
    "results",
    "returns",
    "schedule",
    "startlist",
    "withdrawal",
    "withdraws",
    "won",
    "wins",
    "абдей",
    "заяв",
    "итог",
    "квалифиц",
    "маршрут",
    "обнов",
    "оконча",
    "открыл",
    "отмен",
    "перен",
    "побед",
    "подтверд",
    "прие",
    "приз",
    "результ",
    "рекорд",
    "снял",
    "состав",
    "старт",
    "травм",
    "участник",
    "финал",
}


def story_tokens(text: str) -> set[str]:
    tokens = {token.lower() for token in TOKEN_RE.findall(text)}
    return {token for token in tokens if len(token) >= 3 and token not in STOP_WORDS}


def story_similarity(left: str, right: str) -> float:
    left_tokens = story_tokens(left)
    right_tokens = story_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def is_meaningful_update(item: SourceItem) -> bool:
    text = f"{item.title} {item.summary}".lower()
    return any(term in text for term in UPDATE_TERMS)


def find_related_story(
    item: SourceItem,
    candidates: list[StoryCandidate],
    threshold: float,
) -> StoryCandidate | None:
    current_story = f"{item.title} {item.summary}"
    best_candidate: StoryCandidate | None = None
    best_score = 0.0
    for candidate in candidates:
        if candidate.source_url == item.url:
            continue
        candidate_story = f"{candidate.title} {candidate.text}"
        score = story_similarity(current_story, candidate_story)
        if score > best_score:
            best_score = score
            best_candidate = candidate
    if best_candidate is None or best_score < threshold:
        return None
    return best_candidate


def telegram_post_url(channel_id: str, message_id: int | None) -> str | None:
    if message_id is None or not channel_id.startswith("@"):
        return None
    return f"https://t.me/{channel_id[1:]}/{message_id}"
