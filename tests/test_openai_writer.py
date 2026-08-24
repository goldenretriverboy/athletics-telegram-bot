from app.core.config import Settings
from app.models import SourceItem
from app.writer.openai_writer import (
    build_draft_prompt,
    build_response_params,
    extract_readable_text,
    sanitize_generated_text,
    select_draft_model,
)


def make_settings() -> Settings:
    return Settings(
        database_url="postgresql://example",
        telegram_bot_token="token",
        telegram_channel_id="channel",
        telegram_draft_chat_id="draft",
        telegram_webhook_secret="a-secure-secret-value",
        openai_api_key="key",
        openai_model="gpt-5.6-sol",
        openai_hourly_model="gpt-5.6-sol",
        openai_strong_model="gpt-5.6-sol",
    )


def test_select_draft_model_uses_hourly_model_for_hourly_posts() -> None:
    assert select_draft_model(make_settings(), "hourly") == "gpt-5.6-sol"


def test_select_draft_model_uses_strong_model_for_morning_digest() -> None:
    assert select_draft_model(make_settings(), "morning") == "gpt-5.6-sol"


def test_select_draft_model_uses_strong_model_for_analysis() -> None:
    assert select_draft_model(make_settings(), "analysis") == "gpt-5.6-sol"


def test_extract_readable_text_ignores_scripts_and_keeps_article_text() -> None:
    html = """
    <html>
      <script>tracking()</script>
      <body>
        <nav>Menu</nav>
        <article>
          <h1>Race result</h1>
          <p>Winner ran 2:04:31 in Berlin.</p>
          <p>The course record stayed intact.</p>
        </article>
      </body>
    </html>
    """

    text = extract_readable_text(html)

    assert "tracking" not in text
    assert "Menu" not in text
    assert "Winner ran 2:04:31 in Berlin." in text
    assert "The course record stayed intact." in text


def test_build_draft_prompt_includes_article_context_instruction() -> None:
    item = SourceItem(
        source_id="test",
        source_name="World Athletics",
        title="Race result",
        url="https://example.com/race",
        summary="Short summary",
        published_at=None,
        content_hash="hash",
    )

    prompt = build_draft_prompt(
        item=item,
        editorial_rules="No template phrases.",
        mode="hourly",
        article_context="Winner ran 2:04:31 in Berlin.",
    )

    assert "Article text excerpt:" in prompt
    assert "Winner ran 2:04:31 in Berlin." in prompt
    assert "internally extract the strongest source-backed facts" in prompt


def test_build_response_params_enables_web_search() -> None:
    params = build_response_params("gpt-5.6-sol", "Write post", web_search_enabled=True)

    assert params["model"] == "gpt-5.6-sol"
    assert params["input"] == "Write post"
    assert params["tools"] == [{"type": "web_search"}]


def test_sanitize_generated_text_removes_source_lines_and_raw_urls() -> None:
    text = sanitize_generated_text(
        "Runner's World разобрал силовую подготовку для masters-бегунов.\n\n"
        "В статье есть приседания, выпады и работа на корпус.\n\n"
        "Источник: https://www.runnersworld.com/training/example\n"
        "Источник: Runner's World"
    )

    assert "Runner's World разобрал" in text
    assert "приседания" in text
    assert "Источник:" not in text
    assert "https://" not in text
