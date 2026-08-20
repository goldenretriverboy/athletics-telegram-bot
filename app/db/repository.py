from __future__ import annotations

from collections.abc import Sequence

import asyncpg

from app.core.hashing import stable_hash
from app.models import DraftPost, SourceItem


async def insert_source_items(pool: asyncpg.Pool, items: Sequence[SourceItem]) -> list[SourceItem]:
    saved: list[SourceItem] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await conn.fetchrow(
                """
                INSERT INTO source_items (
                    source_id, source_name, title, url, summary, published_at, content_hash, score
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (url) DO NOTHING
                RETURNING id
                """,
                item.source_id,
                item.source_name,
                item.title,
                item.url,
                item.summary,
                item.published_at,
                item.content_hash,
                item.score,
            )
            if row:
                item.id = row["id"]
                saved.append(item)
    return saved


async def draft_exists_for_source(pool: asyncpg.Pool, source_url: str) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT 1 FROM drafts WHERE source_url = $1 LIMIT 1", source_url)
    return row is not None


async def insert_draft(pool: asyncpg.Pool, draft: DraftPost) -> DraftPost:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO drafts (
                source_item_id, text, source_url, source_title, disable_web_page_preview
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            draft.source_item_id,
            draft.text,
            draft.source_url,
            draft.source_title,
            draft.disable_web_page_preview,
        )
    draft.id = row["id"]
    return draft


async def get_draft(pool: asyncpg.Pool, draft_id: int) -> DraftPost | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, source_item_id, text, source_url, source_title, disable_web_page_preview
            FROM drafts
            WHERE id = $1
            """,
            draft_id,
        )
    if not row:
        return None
    return DraftPost(
        id=row["id"],
        source_item_id=row["source_item_id"],
        text=row["text"],
        source_url=row["source_url"],
        source_title=row["source_title"],
        disable_web_page_preview=row["disable_web_page_preview"],
    )


async def mark_draft_status(pool: asyncpg.Pool, draft_id: int, status: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE drafts SET status = $1, updated_at = NOW() WHERE id = $2",
            status,
            draft_id,
        )


async def mark_draft_message(pool: asyncpg.Pool, draft_id: int, message_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE drafts SET telegram_message_id = $1, updated_at = NOW() WHERE id = $2",
            message_id,
            draft_id,
        )


async def insert_published_post(
    pool: asyncpg.Pool,
    draft: DraftPost,
    telegram_message_id: int | None,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO published_posts (
                draft_id, source_url, source_title, text_hash, telegram_message_id
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (text_hash) DO NOTHING
            """,
            draft.id,
            draft.source_url,
            draft.source_title,
            stable_hash(draft.text),
            telegram_message_id,
        )
