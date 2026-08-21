# Troubleshooting

## Бот Не Создал Черновики

Симптом:

```json
{"ok":true,"created":0}
```

Это не всегда ошибка.

Возможные причины:

- нет сильных новостей;
- новости уже были использованы раньше;
- hourly-фильтр отсёк item-ы ниже score threshold;
- RSS-источник временно пустой или недоступен;
- OpenAI/Railway/Telegram вернули ошибку, но она видна только в логах.

Что проверить:

1. Railway logs web service или cron-сервиса.
2. Есть ли свежие item-ы в RSS-источниках.
3. Не слишком строгие `watch_terms` или `min_score`.
4. Таблицу `drafts`, нет ли уже черновиков по тем же source URL.
5. Таблицу `source_items`, сохраняются ли новые источники.

## Cron Не Сработал

Проверить:

- существует ли отдельный Railway service для job;
- задан ли `cronSchedule`;
- есть ли `nextCronRunAt`;
- задан ли `RAILWAY_RUN_COMMAND`;
- последний deployment job-сервиса в статусе `SUCCESS`;
- нет ли инцидента Railway.

Важно: cron uses UTC.

Для Алматы:

- 09:00 = 04:00 UTC;
- 10:00 = 05:00 UTC;
- 22:00 = 17:00 UTC.

## Cron Запускает Web Server Вместо Job

Причина: не задан `RAILWAY_RUN_COMMAND`.

Проверить переменную в нужном Railway service:

```env
RAILWAY_RUN_COMMAND=python -m app.jobs.digest morning
```

или:

```env
RAILWAY_RUN_COMMAND=python -m app.jobs.hourly
```

## Кнопка Опубликовать Публикует Не Туда

Проверить:

1. `TELEGRAM_CHANNEL_ID`.
2. `TELEGRAM_DRAFT_CHAT_ID`.
3. Railway variables именно у web service.
4. Был ли redeploy после изменения variables.
5. Бот добавлен администратором в основной канал.

Если `TELEGRAM_CHANNEL_ID` равен draft chat id, публикация уйдёт обратно в draft-канал.

## Telegram Webhook Не Работает

Проверить:

1. `PUBLIC_BASE_URL`.
2. `/health`.
3. `TELEGRAM_WEBHOOK_SECRET`.
4. Срабатывает ли `scripts/set_telegram_webhook.py`.
5. Telegram Bot API `getWebhookInfo`.

Webhook принимает только callback updates. Обычные сообщения в чат не обрабатываются.

## 401 На Admin Endpoint

Причина: неверный или отсутствующий header.

Нужно:

```text
X-Admin-Secret: <TELEGRAM_WEBHOOK_SECRET>
```

## OpenAI Ошибка

Проверить:

- `OPENAI_API_KEY`;
- баланс OpenAI API;
- `OPENAI_MODEL`;
- доступность модели;
- Railway logs.

Если баланс пополнен, но ошибки продолжаются, нужен redeploy или restart сервиса, чтобы переменные точно применились.

## Локальные Тесты Не Запускаются

Если ошибка связана с Python 3.9:

```text
ImportError: cannot import name 'UTC' from 'datetime'
```

или:

```text
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

Значит используется старый Python. Нужно активировать `.venv`:

```bash
source .venv/bin/activate
python --version
```

Ожидается `3.12.x`.

## Секрет Попал В Чат Или Скриншот

Нужно перевыпустить:

- Telegram bot token через BotFather;
- OpenAI API key через OpenAI dashboard;
- webhook secret в Railway variables.

После замены:

1. обновить Railway variables;
2. redeploy web service и cron services;
3. обновить локальный `.env`;
4. заново установить Telegram webhook.

