from src.message_builder import build_telegram_message
from src.models import CuratedArticle


def make_article(
    title: str = "Original AI Title",
    source: str = "Example",
    relevance_score: int = 9,
    recommendation_reasons=None,
    url: str = "https://example.com/article",
) -> CuratedArticle:
    return CuratedArticle(
        title=title,
        source=source,
        url=url,
        snippet="Google Alerts snippet with original English source text.",
        relevance_score=relevance_score,
        why_selected=(
            "신뢰도 높은 출처(Example) / 주요 신호: AI Interface Shift / "
            "보조 신호: Semiconductor Race. 알림 요약 근거: Google Alerts snippet. "
            "이는 검색 인터페이스 변화가 AI 서비스 유통 경로를 바꾸는 신호일 수 있습니다."
        ),
        korean_summary="한국어 요약입니다.",
        career_market_insight="커리어와 시장 인사이트입니다.",
        recommendation_reasons=recommendation_reasons
        if recommendation_reasons is not None
        else ["신뢰도 높은 출처", "가격 / 비용 변화", "기업 도입"],
    )


def test_empty_list_returns_empty_string() -> None:
    assert build_telegram_message([]) == ""


def test_message_includes_final_header() -> None:
    message = build_telegram_message([make_article()])

    assert "Daily High-Signal Tech Alerts" in message


def test_message_uses_circled_numbering_for_top_3() -> None:
    message = build_telegram_message(
        [
            make_article("First"),
            make_article("Second"),
            make_article("Third"),
        ]
    )

    assert "① " in message
    assert "② " in message
    assert "③ " in message


def test_message_falls_back_to_normal_numbering_after_top_3() -> None:
    message = build_telegram_message(
        [
            make_article("First"),
            make_article("Second"),
            make_article("Third"),
            make_article("Fourth"),
        ]
    )

    assert "4. " in message


def test_message_uses_stars_not_numeric_score() -> None:
    message = build_telegram_message([make_article(relevance_score=12)])

    assert "⭐⭐⭐⭐⭐" in message
    assert "12" not in message
    assert "관련도 점수" not in message


def test_message_renders_full_english_title() -> None:
    title = "Google Shifts to AI Search, Heralding Major Change in How People Use the Internet"

    message = build_telegram_message([make_article(title)])

    assert title in message


def test_message_renders_source_without_icon_label() -> None:
    message = build_telegram_message([make_article(source="Reuters")])

    assert "Reuters" in message
    assert "📂" not in message


def test_empty_source_is_hidden() -> None:
    message = build_telegram_message([make_article(source="  ")])

    assert "\n  \n" not in message
    assert "📂" not in message


def test_recommendation_reasons_render_under_selection_points() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["신뢰도 높은 출처", "가격 / 비용 변화", "기업 도입"]
            )
        ]
    )

    assert "선정 포인트" in message
    assert "• 신뢰도 높은 출처" in message
    assert "• 가격 / 비용 변화" in message
    assert "• 기업 도입" in message


def test_empty_recommendation_reasons_hide_selection_points() -> None:
    message = build_telegram_message([make_article(recommendation_reasons=[])])

    assert "선정 포인트" not in message


def test_quality_pass_reason_is_never_rendered() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["저품질 패턴 없음", "신뢰도 높은 출처"]
            )
        ]
    )

    assert "저품질 패턴 없음" not in message
    assert "• 신뢰도 높은 출처" in message


def test_recommendation_reasons_are_capped_to_3() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=[
                    "신뢰도 높은 출처",
                    "가격 / 비용 변화",
                    "기업 도입",
                    "보안 사고",
                ]
            )
        ]
    )

    assert "• 신뢰도 높은 출처" in message
    assert "• 가격 / 비용 변화" in message
    assert "• 기업 도입" in message
    assert "보안 사고" not in message


def test_internal_labels_are_not_rendered() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=[
                    "AI Interface Shift",
                    "Semiconductor Race",
                    "반도체 공급망",
                ]
            )
        ]
    )

    assert "AI Interface Shift" not in message
    assert "Semiconductor Race" not in message
    assert "• 반도체 공급망" in message


def test_old_labels_are_absent() -> None:
    message = build_telegram_message([make_article()])

    assert "선정 이유" not in message
    assert "커리어 / 시장 인사이트" not in message
    assert "Why it Matters" not in message
    assert "Google Alerts" not in message
    assert "근거:" not in message
    assert "📝 Google Alerts" not in message
    assert "💡 Why it Matters" not in message
    assert "주요 신호" not in message
    assert "보조 신호" not in message
    assert "AI Interface Shift" not in message


def test_separator_appears_between_articles_only() -> None:
    message = build_telegram_message([make_article("First"), make_article("Second")])

    assert message.count("────────────") == 1
    assert not message.endswith("────────────")


def test_link_uses_plain_read_label_without_markdown_parse_mode() -> None:
    message = build_telegram_message([make_article(url="https://example.com/article")])

    assert "🔗 Read\nhttps://example.com/article" in message
    assert "[Read]" not in message
