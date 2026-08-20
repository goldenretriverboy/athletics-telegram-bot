from app.telegram.formatting import append_source, make_draft_keyboard


def test_append_source_escapes_html() -> None:
    text = append_source("Текст", "https://example.com/?a=1&b=2", "A&B")
    assert "Источник: A&amp;B" in text
    assert "https://example.com/?a=1&amp;b=2" in text


def test_make_draft_keyboard_contains_actions() -> None:
    keyboard = make_draft_keyboard(42)
    buttons = [button for row in keyboard["inline_keyboard"] for button in row]
    assert {"text": "Опубликовать", "callback_data": "publish:42"} in buttons
    assert {"text": "Отклонить", "callback_data": "reject:42"} in buttons
    assert {"text": "Переписать", "callback_data": "rewrite:42"} in buttons

