CREATE TABLE IF NOT EXISTS source_items (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL DEFAULT '',
    published_at TIMESTAMPTZ,
    content_hash TEXT NOT NULL UNIQUE,
    score INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drafts (
    id BIGSERIAL PRIMARY KEY,
    source_item_id BIGINT REFERENCES source_items(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    text TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    disable_web_page_preview BOOLEAN NOT NULL DEFAULT FALSE,
    telegram_message_id BIGINT,
    rewrite_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS published_posts (
    id BIGSERIAL PRIMARY KEY,
    draft_id BIGINT REFERENCES drafts(id) ON DELETE SET NULL,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    text_hash TEXT NOT NULL UNIQUE,
    telegram_message_id BIGINT,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS run_logs (
    id BIGSERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

