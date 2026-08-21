# Railway

Production живёт на Railway.

## Сервисы

Проект использует несколько Railway services:

- `athletics-telegram-bot`: web service;
- `morning-digest`: scheduled job для утренней сводки;
- `hourly-monitor`: scheduled job для мониторинга;
- `Postgres`: база данных.

## Web Service

Команда по умолчанию задаётся в `railway.json`:

```bash
uvicorn app.web.main:app --host 0.0.0.0 --port ${PORT}
```

Health check:

```text
GET /health
```

Production URL:

```text
https://athletics-telegram-bot-production.up.railway.app
```

## Scheduled Jobs

Railway cron использует UTC.

Проектный timezone: `Asia/Almaty`, UTC+5.

### Morning Digest

Назначение: утренняя тематическая сводка.

Команда:

```bash
python -m app.jobs.digest morning
```

Расписание:

```text
0 4 * * *
```

Это 09:00 по Алматы.

### Hourly Monitor

Назначение: проверять важные новости в течение дня.

Команда:

```bash
python -m app.jobs.hourly
```

Расписание:

```text
0 5-17 * * *
```

Это 10:00-22:00 по Алматы.

Если нужно начинать в 09:00 по Алматы, cron должен быть:

```text
0 4-17 * * *
```

## `RAILWAY_RUN_COMMAND`

Cron-сервисы используют тот же repo, что и web service. Поэтому для каждого cron-сервиса должна быть переменная:

```env
RAILWAY_RUN_COMMAND=python -m app.jobs.digest morning
```

или:

```env
RAILWAY_RUN_COMMAND=python -m app.jobs.hourly
```

Без этой переменной cron-сервис может стартовать как web server, а не как job.

## Railway Variables

Переменные задаются в `production` environment.

Минимальный набор:

```text
APP_ENV
LOG_LEVEL
AUTO_PUBLISH
DATABASE_URL
PUBLIC_BASE_URL
TELEGRAM_BOT_TOKEN
TELEGRAM_CHANNEL_ID
TELEGRAM_DRAFT_CHAT_ID
TELEGRAM_WEBHOOK_SECRET
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_HOURLY_MODEL
OPENAI_STRONG_MODEL
TIMEZONE
MAX_DRAFTS_PER_RUN
```

Для cron-сервисов дополнительно:

```text
RAILWAY_RUN_COMMAND
```

## Проверка Деплоя

Через Railway CLI:

```bash
npx @railway/cli deployment list \
  --project 20432632-af86-4fe3-b4fa-2e50b142ae63 \
  --environment production \
  --service bfca44a7-16e0-4250-81b3-0991c8f0582f \
  --limit 5
```

Проверка health:

```bash
curl https://athletics-telegram-bot-production.up.railway.app/health
```

Ожидаемый ответ:

```json
{"ok":true}
```

## Логи

Web logs:

```bash
npx @railway/cli logs \
  --deployment \
  --lines 160 \
  --project 20432632-af86-4fe3-b4fa-2e50b142ae63 \
  --environment production \
  --service bfca44a7-16e0-4250-81b3-0991c8f0582f
```

Для cron-сервисов меняется только `--service`.

## После Push В GitHub

Railway обычно сам подхватывает новый commit и redeploy-ит сервисы.

После push нужно проверить:

1. Web service собрался успешно.
2. `morning-digest` собрался успешно.
3. `hourly-monitor` собрался успешно.
4. `/health` отвечает `{"ok":true}`.
5. Ручной admin run работает, если менялся pipeline.
