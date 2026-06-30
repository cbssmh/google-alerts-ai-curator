from src.message_builder import build_telegram_message
from src.models import CuratedArticle


def make_article(
    title: str = "Original AI Title",
    source: str = "Example",
    snippet: str = "Google Alerts snippet with original English source text.",
    relevance_score: int = 9,
) -> CuratedArticle:
    return CuratedArticle(
        title=title,
        source=source,
        url="https://example.com/article",
        snippet=snippet,
        relevance_score=relevance_score,
        why_selected=(
            "신뢰도 높은 출처(Example) / 주요 신호: AI Interface Shift / "
            "보조 신호: Semiconductor Race. 알림 요약 근거: Google Alerts snippet. "
            "이는 검색 인터페이스 변화가 AI 서비스 유통 경로를 바꾸는 신호일 수 있습니다."
        ),
        korean_summary="한국어 요약입니다.",
        career_market_insight="커리어와 시장 인사이트입니다.",
    )


def test_empty_list_returns_empty_string() -> None:
    assert build_telegram_message([]) == ""


def test_message_includes_header() -> None:
    message = build_telegram_message([make_article()])

    assert "Daily AI Curated News Top 3" in message


def test_message_includes_original_title() -> None:
    message = build_telegram_message([make_article("Original Article Title")])

    assert "Original Article Title" in message


def test_message_uses_reader_facing_card_labels() -> None:
    message = build_telegram_message([make_article()])

    assert "📰" in message
    assert "📂" in message
    assert "📝 Google Alerts" in message
    assert "💡 Why it Matters" in message
    assert "🔗 Read" in message


def test_empty_source_does_not_render_source_block() -> None:
    message = build_telegram_message([make_article(source="  ")])

    assert "📂" not in message


def test_non_empty_source_renders_source_block() -> None:
    message = build_telegram_message([make_article(source="Example")])

    assert "📂 Example" in message


def test_message_hides_internal_labels_and_old_fields() -> None:
    message = build_telegram_message([make_article()])

    assert "관련도 점수" not in message
    assert "선정 이유" not in message
    assert "커리어 / 시장 인사이트" not in message
    assert "주요 신호" not in message
    assert "보조 신호" not in message
    assert "AI Interface Shift" not in message
    assert "Semiconductor Race" not in message
    assert "relevance_score" not in message


def test_message_hides_score_value() -> None:
    message = build_telegram_message([make_article(relevance_score=42)])

    assert "42" not in message


def test_message_includes_snippet_under_google_alerts() -> None:
    article = make_article()

    message = build_telegram_message([article])

    assert "📝 Google Alerts\nGoogle Alerts snippet with original English source text." in message


def test_message_includes_evidence_when_snippet_exists() -> None:
    message = build_telegram_message([make_article()])

    assert "근거: Google Alerts snippet with original English source text." in message


def test_message_omits_evidence_when_snippet_is_empty() -> None:
    message = build_telegram_message([make_article(snippet="  ")])

    assert "근거:" not in message


def test_evidence_is_shorter_than_full_snippet() -> None:
    snippet = (
        "Google announced a boatload of new AI -powered features at its I/O keynote, "
        "but most of them will launch behind paywalls. "
        "This extra sentence should not fully appear in the evidence line."
    )

    message = build_telegram_message([make_article(snippet=snippet)])
    evidence_line = next(line for line in message.splitlines() if line.startswith("근거:"))

    assert "AI-powered" in message
    assert evidence_line.startswith("근거: Google announced")
    assert "This extra sentence should not fully appear in the evidence line." not in evidence_line


def test_link_appears_after_read_label() -> None:
    message = build_telegram_message([make_article()])

    assert "🔗 Read\nhttps://example.com/article" in message


def test_multiple_articles_repeat_article_cards() -> None:
    message = build_telegram_message([make_article("First"), make_article("Second")])

    assert "📰 First" in message
    assert "📰 Second" in message
