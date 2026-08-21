# Документация

Это центральная папка документации проекта `athletics-telegram-bot`.

## Навигация

- [Обзор проекта](overview.md): назначение, роли сервисов, общий поток данных.
- [Локальная разработка](local-development.md): как поднять окружение, запускать тесты и сервер.
- [Конфигурация](configuration.md): `.env`, Railway variables, `config/sources.yaml`, `config/editorial.md`.
- [Railway](railway.md): web service, cron jobs, Postgres, деплой и логи.
- [Telegram](telegram.md): draft-канал, основной канал, webhook, кнопки.
- [Редакционные правила](editorial.md): фокус на бег, стиль постов, источники, картинки.
- [Операции](operations.md): ежедневная работа, ручные запуски, проверки после деплоя.
- [Troubleshooting](troubleshooting.md): что проверять, если бот не создаёт или не публикует посты.

## Главные Файлы Проекта

- `app/web/main.py`: FastAPI-приложение и подключение роутеров.
- `app/web/admin.py`: защищённые admin endpoints для ручных запусков.
- `app/telegram/webhook.py`: обработка callback-кнопок Telegram.
- `app/telegram/client.py`: отправка черновиков и публикаций через Telegram Bot API.
- `app/pipeline.py`: основной pipeline сбора источников, ранжирования, генерации и отправки.
- `app/writer/openai_writer.py`: генерация текста через OpenAI API.
- `app/ranking/scorer.py`: правила приоритизации новостей.
- `app/db/repository.py`: операции с Postgres.
- `config/sources.yaml`: RSS-источники и watch terms.
- `config/editorial.md`: редакционные правила для OpenAI prompt.
- `migrations/001_init.sql`: схема базы.
- `railway.json`: Railway start command.
- `scripts/run_migrations.py`: применение SQL-миграций.
- `scripts/set_telegram_webhook.py`: установка Telegram webhook.

## Принцип Работы

1. Cron job или admin endpoint запускает pipeline.
2. Pipeline читает RSS-источники из `config/sources.yaml`.
3. Новости получают score по приоритетам источника, важным словам и watch terms.
4. Уже использованные source URL не создают повторные черновики.
5. OpenAI пишет текст по правилам из `config/editorial.md`.
6. Черновик сохраняется в Postgres и отправляется в `TELEGRAM_DRAFT_CHAT_ID`.
7. Редактор нажимает `Опубликовать`, `Отклонить` или `Переписать`.
8. `Опубликовать` отправляет пост в `TELEGRAM_CHANNEL_ID`.

