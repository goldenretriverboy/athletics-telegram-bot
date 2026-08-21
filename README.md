# athletics-telegram-bot

Telegram-бот для канала `@beyond_the_1ine`: он собирает новости про бег и лёгкую атлетику, пишет русскоязычные черновики через OpenAI API, отправляет их в draft-канал на согласование и публикует в основной канал только после нажатия кнопки `Опубликовать`.

Главная идея проекта: не спамить ленту. Утром бот готовит более крупную тематическую сводку, а в течение дня отслеживает источники и создаёт черновики только по важным поводам.

## Быстрый Старт

Рабочая папка на локальной машине:

```bash
cd /Users/ignat.yaskevich/Development/pet-projects/athletics-telegram-bot
source .venv/bin/activate
```

Проверить проект:

```bash
python -m pytest
python -m ruff check .
```

Запустить локальный API:

```bash
uvicorn app.web.main:app --reload
```

Запустить миграции для базы из текущего `.env`:

```bash
python scripts/run_migrations.py
```

Важно: локальный `.env` содержит production-ключи. Не коммить его и осторожно запускай команды, которые могут писать в реальный Telegram.

## Где Документация

Вся подробная документация лежит в [`docs/`](docs/README.md).

- [`docs/README.md`](docs/README.md): карта документации.
- [`docs/overview.md`](docs/overview.md): что делает проект и как устроен поток данных.
- [`docs/local-development.md`](docs/local-development.md): локальная настройка, тесты, команды.
- [`docs/configuration.md`](docs/configuration.md): переменные окружения и конфиги.
- [`docs/railway.md`](docs/railway.md): Railway-сервисы, cron, деплой.
- [`docs/telegram.md`](docs/telegram.md): Telegram-каналы, webhook, кнопки черновиков.
- [`docs/editorial.md`](docs/editorial.md): редакционные правила постов.
- [`docs/operations.md`](docs/operations.md): ежедневная эксплуатация и ручные запуски.
- [`docs/troubleshooting.md`](docs/troubleshooting.md): частые проблемы и диагностика.

## Production

Production работает на Railway:

- web service: FastAPI, `/health`, Telegram webhook и admin endpoints;
- `morning-digest`: cron для утренней сводки;
- `hourly-monitor`: cron для мониторинга важных новостей в течение дня;
- Postgres: источники, черновики, опубликованные посты;
- Telegram Bot API: draft approval и публикация;
- OpenAI API: генерация текста черновиков.

Публикация по умолчанию ручная: `AUTO_PUBLISH=false`.

## Основные Команды

Ручной запуск hourly-мониторинга через web endpoint:

```bash
curl -X POST \
  -H "X-Admin-Secret: $TELEGRAM_WEBHOOK_SECRET" \
  "$PUBLIC_BASE_URL/admin/run/hourly"
```

Ручной запуск утренней сводки:

```bash
curl -X POST \
  -H "X-Admin-Secret: $TELEGRAM_WEBHOOK_SECRET" \
  "$PUBLIC_BASE_URL/admin/run/digest/morning"
```

Тестовый черновик в draft-канал:

```bash
curl -X POST \
  -H "X-Admin-Secret: $TELEGRAM_WEBHOOK_SECRET" \
  "$PUBLIC_BASE_URL/admin/test-draft"
```

## Безопасность

- Не публикуй `.env`, Telegram token, OpenAI key, `DATABASE_URL`, webhook secret.
- `AUTO_PUBLISH=false` должен оставаться стандартным режимом.
- Бот должен иметь права администратора только там, где он реально нужен.
- Если токен был отправлен в чат или попал в скриншот, его нужно перевыпустить.
