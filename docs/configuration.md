# Конфигурация

Конфигурация проекта состоит из трёх частей:

- environment variables;
- `config/sources.yaml`;
- `config/editorial.md`.

## Environment Variables

Класс настроек: `app/core/config.py`.

Локально переменные читаются из `.env`. В production они задаются в Railway.

| Переменная | Обязательная | Назначение |
| --- | --- | --- |
| `APP_ENV` | Нет | Имя окружения. Обычно `production` или `development`. |
| `LOG_LEVEL` | Нет | Уровень логов. Обычно `INFO`. |
| `AUTO_PUBLISH` | Нет | Если `true`, бот публикует сразу. Стандартно `false`. |
| `PUBLIC_BASE_URL` | Да для webhook | Публичный URL web-сервиса Railway. |
| `DATABASE_URL` | Да | Postgres connection string. |
| `TELEGRAM_BOT_TOKEN` | Да | Token Telegram-бота от BotFather. |
| `TELEGRAM_CHANNEL_ID` | Да | Основной канал для публикаций, например `@beyond_the_1ine`. |
| `TELEGRAM_DRAFT_CHAT_ID` | Да | Draft-канал или чат, куда приходят черновики. |
| `TELEGRAM_WEBHOOK_SECRET` | Да | Secret для Telegram webhook и admin endpoints. Минимум 16 символов. |
| `OPENAI_API_KEY` | Да | API key для OpenAI API. |
| `OPENAI_MODEL` | Нет | Fallback-модель для генерации черновиков. |
| `OPENAI_HOURLY_MODEL` | Нет | Модель для hourly monitoring. Сейчас `gpt-5.6-sol`. |
| `OPENAI_STRONG_MODEL` | Нет | Модель для утренних сводок и аналитических постов. Сейчас `gpt-5.6-sol`. |
| `OPENAI_WEB_SEARCH_ENABLED` | Нет | Если `true`, модель может использовать web search перед написанием поста. Сейчас `true`. |
| `TIMEZONE` | Нет | Часовой пояс проекта. Сейчас `Asia/Almaty`. |
| `MAX_DRAFTS_PER_RUN` | Нет | Максимум новых черновиков за один запуск. |
| `HOURLY_NO_NEWS_STATUS_ENABLED` | Нет | Если `true`, draft-чат получает редкий служебный статус, когда hourly несколько раз подряд не создал черновики. |
| `HOURLY_NO_NEWS_NOTIFY_AFTER_RUNS` | Нет | Через сколько пустых hourly-проверок отправлять статус. Сейчас `4`. |
| `DUPLICATE_STORY_LOOKBACK_DAYS` | Нет | Сколько дней назад смотреть draft/опубликованные посты, чтобы не повторять одну и ту же историю. Сейчас `14`. |
| `DUPLICATE_STORY_SIMILARITY_THRESHOLD` | Нет | Порог похожести для определения одной истории. Сейчас `0.42`. |

## Важные Безопасные Значения

```env
AUTO_PUBLISH=false
TIMEZONE=Asia/Almaty
MAX_DRAFTS_PER_RUN=3
HOURLY_NO_NEWS_STATUS_ENABLED=true
HOURLY_NO_NEWS_NOTIFY_AFTER_RUNS=4
DUPLICATE_STORY_LOOKBACK_DAYS=14
DUPLICATE_STORY_SIMILARITY_THRESHOLD=0.42
```

`AUTO_PUBLISH=false` означает, что бот отправляет черновики в draft-канал и ждёт ручного подтверждения.

## OpenAI Model Routing

Модель выбирается по режиму запуска:

- `hourly`: `OPENAI_HOURLY_MODEL`, сейчас `gpt-5.6-sol`;
- `morning`: `OPENAI_STRONG_MODEL`, сейчас `gpt-5.6-sol`;
- `analysis` и `explainer`: `OPENAI_STRONG_MODEL`;
- если отдельная модель не задана, используется fallback `OPENAI_MODEL`.

Так все режимы генерации используют одну сильную модель. Это дороже, но полезно, если hourly posts тоже должны выходить как полноценные русскоязычные мини-статьи.

Если `OPENAI_WEB_SEARCH_ENABLED=true`, writer разрешает OpenAI web search. Модель может искать недостающие результаты, даты, исследования и официальный контекст перед написанием поста.

## No-News Status

Hourly monitoring часто должен возвращать `created=0`: это значит, что слабые, повторные или уже обработанные новости были пропущены.

Чтобы было видно, что cron живой, `HOURLY_NO_NEWS_STATUS_ENABLED=true` включает служебное сообщение в draft-чат после нескольких пустых проверок подряд. По умолчанию статус отправляется после 4 пустых hourly runs, затем после 8, 12 и так далее.

## Повторы И Апдейты

Перед созданием draft бот проверяет последние draft/опубликованные посты за `DUPLICATE_STORY_LOOKBACK_DAYS`.

Если новая статья похожа на уже обработанную историю и в заголовке/summary нет явного апдейта, она пропускается. Апдейтом считаются результаты, рекорды, отмены, переносы, регистрация, жеребьёвка, состав элиты, травмы, снятия, изменения маршрута, призовые и другие факты, которые реально меняют историю.

Если это похожая история, но в ней есть апдейт, draft создаётся как продолжение: writer получает контекст прошлого поста и должен объяснить, что изменилось сейчас. Если прошлый пост уже опубликован в основном канале и у него есть `telegram_message_id`, бот добавляет ссылку `Предыдущий пост по теме`.

## `config/sources.yaml`

Файл содержит:

- список RSS-источников;
- `watch_terms` для повышения score важных тем.

Структура источника:

```yaml
- id: world-athletics-news
  name: World Athletics
  type: rss
  url: https://worldathletics.org/feeds/news
  priority: 100
```

Поля:

- `id`: стабильный технический id;
- `name`: название источника для source link;
- `type`: сейчас используется `rss`;
- `url`: RSS URL;
- `priority`: базовый score источника.

Чтобы добавить источник:

1. Добавь запись в `sources`.
2. Проверь, что RSS реально отдаёт item-ы.
3. Запусти тестовый hourly или morning run.
4. Убедись, что черновики не засоряют канал.

## `config/editorial.md`

Это редакционные правила, которые напрямую попадают в prompt OpenAI.

Если нужно изменить стиль постов, сначала правим `config/editorial.md`.

## `railway.json`

Файл задаёт start command:

```json
"startCommand": "sh -c \"${RAILWAY_RUN_COMMAND:-uvicorn app.web.main:app --host 0.0.0.0 --port ${PORT}}\""
```

Это важно: один и тот же repo используется для web service и cron-сервисов.

- Если `RAILWAY_RUN_COMMAND` не задан, стартует web server.
- Если `RAILWAY_RUN_COMMAND` задан, Railway запускает job command.
