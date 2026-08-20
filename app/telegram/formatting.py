import html


def append_source(text: str, source_url: str, source_title: str) -> str:
    escaped_url = html.escape(source_url, quote=True)
    escaped_title = html.escape(source_title)
    return f"{text.strip()}\n\n<a href=\"{escaped_url}\">Источник: {escaped_title}</a>"


def make_draft_keyboard(draft_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Опубликовать", "callback_data": f"publish:{draft_id}"},
                {"text": "Отклонить", "callback_data": f"reject:{draft_id}"},
            ],
            [{"text": "Переписать", "callback_data": f"rewrite:{draft_id}"}],
        ]
    }

