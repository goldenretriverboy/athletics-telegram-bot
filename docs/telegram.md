# Telegram

Telegram используется для двух вещей:

- draft approval;
- публикация в основной канал.

## Каналы И Чаты

### Draft Chat

Переменная:

```env
TELEGRAM_DRAFT_CHAT_ID
```

Сюда бот отправляет черновики с кнопками. Это безопасная зона для проверки текста.

### Main Channel

Переменная:

```env
TELEGRAM_CHANNEL_ID
```

Сюда бот публикует пост после нажатия `Опубликовать`.

Пример:

```env
TELEGRAM_CHANNEL_ID=@beyond_the_1ine
```

## Права Бота

Бот должен быть администратором:

- в draft-канале, чтобы отправлять черновики;
- в основном канале, чтобы публиковать посты.

Для основного канала достаточно права на публикацию сообщений.

Если при нажатии `Опубликовать` пост уходит не туда, проверить:

1. `TELEGRAM_CHANNEL_ID`;
2. `TELEGRAM_DRAFT_CHAT_ID`;
3. что Railway redeploy уже применил новые variables;
4. что бот добавлен администратором в основной канал.

## Webhook

Endpoint:

```text
POST /api/telegram/webhook
```

Telegram должен отправлять callback updates с secret token:

```text
X-Telegram-Bot-Api-Secret-Token
```

Secret должен совпадать с:

```env
TELEGRAM_WEBHOOK_SECRET
```

Установка webhook:

```bash
source .venv/bin/activate
python scripts/set_telegram_webhook.py
```

Скрипт берёт:

- `PUBLIC_BASE_URL`;
- `TELEGRAM_BOT_TOKEN`;
- `TELEGRAM_WEBHOOK_SECRET`.

И устанавливает:

```text
{PUBLIC_BASE_URL}/api/telegram/webhook
```

## Кнопки Черновика

Файл: `app/telegram/formatting.py`.

Черновик получает inline keyboard:

- `Опубликовать`: callback `publish:{draft_id}`;
- `Отклонить`: callback `reject:{draft_id}`;
- `Переписать`: callback `rewrite:{draft_id}`.

## Что Делает Каждая Кнопка

### Опубликовать

Действия:

1. Webhook получает callback.
2. Проверяет secret.
3. Находит draft в Postgres.
4. Отправляет текст в `TELEGRAM_CHANNEL_ID`.
5. Создаёт запись в `published_posts`.
6. Меняет статус draft на `published`.
7. Показывает Telegram callback answer: `Опубликовано`.

### Отклонить

Действия:

1. Меняет статус draft на `rejected`.
2. Ничего не публикует.
3. Показывает callback answer: `Отклонено`.

### Переписать

Сейчас действие только меняет статус:

```text
rewrite_requested
```

Автоматическая генерация новой версии по кнопке пока не реализована.

## Source Link

Файл: `app/telegram/formatting.py`.

Система сама добавляет HTML-ссылку:

```html
<a href="...">Источник: Source Title</a>
```

Поэтому модель не должна писать `Источник:` или URL внутри текста поста. Если это появилось в черновике, такой пост лучше переписать, а правила prompt нужно ужесточить.

## Link Preview

В `DraftPost` есть поле:

```python
disable_web_page_preview
```

Сейчас OpenAI writer ставит:

```python
disable_web_page_preview=False
```

Это разрешает Telegram показать preview, если Telegram сам его построит.

