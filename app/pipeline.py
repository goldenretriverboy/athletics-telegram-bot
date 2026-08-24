from app.collectors.rss import collect_sources
from app.collectors.sources import load_sources
from app.core.config import get_settings
from app.db.repository import (
    count_consecutive_empty_runs,
    draft_exists_for_source,
    insert_draft,
    insert_run_log,
    insert_source_items,
)
from app.ranking.scorer import rank_items
from app.telegram.client import TelegramClient
from app.writer.openai_writer import write_draft


def should_send_no_news_status(consecutive_empty_runs: int, threshold: int) -> bool:
    return threshold > 0 and consecutive_empty_runs > 0 and consecutive_empty_runs % threshold == 0


async def run_monitor(pool, mode: str = "hourly") -> int:
    settings = get_settings()
    sources, watch_terms = load_sources()
    items = await collect_sources(sources)
    limit = settings.max_drafts_per_run
    min_score = None
    if mode == "hourly":
        limit = min(settings.max_drafts_per_run, 2)
        min_score = 115
    ranked = rank_items(items, watch_terms, len(items), min_score=min_score)
    saved_items = await insert_source_items(pool, ranked)

    telegram = TelegramClient()
    created = 0
    for item in saved_items:
        if created >= limit:
            break
        if await draft_exists_for_source(pool, item.url):
            continue
        draft = await write_draft(item, digest_mode=mode)
        draft = await insert_draft(pool, draft)
        if settings.auto_publish:
            message_id = await telegram.publish(draft)
            from app.db.repository import insert_published_post, mark_draft_status

            await insert_published_post(pool, draft, message_id)
            await mark_draft_status(pool, draft.id, "published")
        else:
            message_id = await telegram.send_draft(draft)
            from app.db.repository import mark_draft_message

            await mark_draft_message(pool, draft.id, message_id)
        created += 1
    await insert_run_log(pool, mode, "success", f"created={created}")
    if mode == "hourly" and created == 0 and settings.hourly_no_news_status_enabled:
        empty_runs = await count_consecutive_empty_runs(pool, mode)
        if should_send_no_news_status(empty_runs, settings.hourly_no_news_notify_after_runs):
            await telegram.send_draft_status(
                "Служебный статус: hourly-мониторинг работает. "
                f"Последние {empty_runs} проверки не дали новых сильных тем для draft. "
                "Слабые, повторные или уже обработанные новости пропущены."
            )
    return created
