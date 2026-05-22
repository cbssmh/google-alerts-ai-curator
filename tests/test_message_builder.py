from src.message_builder import build_telegram_message
from src.models import CuratedArticle


def make_article(title: str = "Original AI Title") -> CuratedArticle:
    return CuratedArticle(
        title=title,
        source="Example",
        url="https://example.com/article",
        snippet="",
        relevance_score=9,
        why_selected="중요한 선정 이유",
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


def test_message_includes_korean_summary() -> None:
    message = build_telegram_message([make_article()])

    assert "한국어 요약입니다." in message


def test_message_uses_korean_labels() -> None:
    message = build_telegram_message([make_article()])

    assert "출처:" in message
    assert "링크:" in message
    assert "관련도 점수:" in message
    assert "선정 이유:" in message
    assert "요약:" in message
    assert "커리어 / 시장 인사이트:" in message


def test_multiple_articles_are_numbered() -> None:
    message = build_telegram_message(
        [
            make_article("First"),
            make_article("Second"),
        ]
    )

    assert "1. First" in message
    assert "2. Second" in message
