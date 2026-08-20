# athletics-telegram-bot

Railway-ready Telegram editor bot for the `@beyond_the_1ine` athletics channel.

The service monitors athletics sources, asks OpenAI API to write source-backed Russian drafts, sends drafts to Telegram for approval, and publishes only after approval unless `AUTO_PUBLISH=true`.

## Architecture

- Railway web service: Telegram webhook and health check.
- Railway scheduled jobs: hourly monitoring, morning digest, evening digest.
- Railway Postgres: drafts, published posts, source items, run logs.
- OpenAI API: post writing and formatting from verified facts.
- Telegram Bot API: draft approval and channel publishing.

## Safety Defaults

- `AUTO_PUBLISH=false` by default.
- The bot stores source URLs and content hashes to avoid duplicates.
- Source page images are treated as preview candidates, not reusable photos.
- Secrets are never committed. Use Railway variables.

## Railway Services

Create one web service from this repo:

```bash
uvicorn app.web.main:app --host 0.0.0.0 --port $PORT
```

Create scheduled jobs with these commands. Railway cron uses UTC:

```bash
# 09:00 Asia/Almaty
python -m app.jobs.digest morning

# hourly monitoring, 09:00-22:00 Asia/Almaty = 04:00-17:00 UTC
python -m app.jobs.hourly

# 19:00 Asia/Almaty
python -m app.jobs.digest evening
```

Suggested schedules:

- Morning digest: `0 4 * * *`
- Hourly monitor: `0 4-17 * * *`
- Evening digest: `0 14 * * *`

## Required Variables

Set these in Railway:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (`gpt-4.1-mini` for economical drafts, `gpt-5.5` for higher quality)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `TELEGRAM_DRAFT_CHAT_ID`
- `TELEGRAM_WEBHOOK_SECRET`
- `PUBLIC_BASE_URL`
- `AUTO_PUBLISH=false`

## Local Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/run_migrations.py
pytest
```

## Telegram Webhook

After deploying the web service and setting `PUBLIC_BASE_URL`, run:

```bash
python scripts/set_telegram_webhook.py
```

The webhook endpoint is:

```text
/api/telegram/webhook
```

## Draft Approval Flow

1. Cron job finds and ranks new source items.
2. OpenAI writes draft posts from source-backed facts.
3. Drafts are stored in Postgres.
4. Bot sends draft to `TELEGRAM_DRAFT_CHAT_ID` with buttons:
   - Publish
   - Reject
   - Rewrite
5. Publish sends the post to `TELEGRAM_CHANNEL_ID` and marks it as published.

## Current Status

This is the initial scaffold. The next milestone is connecting real source collectors and testing the approval flow against a private draft chat.
