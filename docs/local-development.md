# Локальная Разработка

Локальный проект находится здесь:

```bash
/Users/ignat.yaskevich/Development/pet-projects/athletics-telegram-bot
```

## Требования

- Python `3.12+`;
- `uv`;
- доступ к GitHub repository;
- `.env` с переменными проекта;
- доступ к Railway/Postgres, если запускаются команды против production.

Проект требует Python `>=3.12`. Системный `python3` на macOS может быть 3.9, его использовать нельзя.

## Первичная Настройка

```bash
cd /Users/ignat.yaskevich/Development/pet-projects/athletics-telegram-bot
uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Проверить версию:

```bash
python --version
```

Ожидается Python `3.12.x`.

## `.env`

Локальный `.env` уже создан из Railway variables.

Нельзя коммитить:

- `.env`;
- Telegram bot token;
- OpenAI API key;
- `DATABASE_URL`;
- `TELEGRAM_WEBHOOK_SECRET`.

Пример безопасного шаблона лежит в `.env.example`.

## Тесты И Линтер

```bash
source .venv/bin/activate
python -m pytest
python -m ruff check .
```

Ожидаемое состояние:

```text
9 passed
All checks passed!
```

## Локальный API

```bash
source .venv/bin/activate
uvicorn app.web.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Ответ:

```json
{"ok":true}
```

## Миграции

Команда применяет SQL-файлы из `migrations/` к базе из `DATABASE_URL`:

```bash
python scripts/run_migrations.py
```

Осторожно: если в `.env` стоит production `DATABASE_URL`, команда работает с production-базой.

## Локальные Ручные Запуски

Можно запускать jobs локально:

```bash
python -m app.jobs.digest morning
python -m app.jobs.hourly
```

Но если `.env` production, эти команды могут:

- создать реальные черновики в Postgres;
- отправить реальные сообщения в draft-канал;
- при `AUTO_PUBLISH=true` опубликовать в основной канал.

Стандартно держим `AUTO_PUBLISH=false`.

## Git Workflow

Проверить состояние:

```bash
git status --short
git branch --show-current
git log --oneline -5
```

Remote:

```bash
git remote -v
```

Ожидаемый remote:

```text
git@github.com:GoldenRetrieverBoy/athletics-telegram-bot.git
```

Перед push:

```bash
python -m pytest
python -m ruff check .
git status --short
```

