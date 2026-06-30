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


def test_numbering_is_not_rendered() -> None:
    message = build_telegram_message(
        [
            make_article("First"),
            make_article("Second"),
            make_article("Third"),
        ]
    )

    assert "①" not in message
    assert "②" not in message
    assert "③" not in message
    assert "1." not in message


def test_recommendation_tier_is_rendered() -> None:
    message = build_telegram_message([make_article(relevance_score=20)])

    assert "🏆 ESSENTIAL" in message


def test_recommendation_tier_mapping_works() -> None:
    essential = build_telegram_message([make_article(relevance_score=20)])
    recommended = build_telegram_message([make_article(relevance_score=8)])
    worth_a_look = build_telegram_message([make_article(relevance_score=4)])

    assert "🏆 ESSENTIAL" in essential
    assert "✅ RECOMMENDED" in recommended
    assert "👀 WORTH A LOOK" in worth_a_look


def test_stars_and_numeric_rating_are_removed() -> None:
    message = build_telegram_message([make_article(relevance_score=23)])

    assert "⭐" not in message
    assert "/5" not in message
    assert "추천도" not in message
    assert "23" not in message
    assert "관련도 점수" not in message


def test_message_renders_full_english_title() -> None:
    title = "Google Shifts to AI Search, Heralding Major Change in How People Use the Internet"

    message = build_telegram_message([make_article(title)])

    assert title in message


def test_article_text_is_html_escaped() -> None:
    message = build_telegram_message(
        [
            make_article(
                title='OpenAI & Google <launch> "AI"',
                recommendation_reasons=["가격 / 비용 변화"],
            )
        ]
    )

    assert "OpenAI &amp; Google &lt;launch&gt; \"AI\"" in message


def test_key_signals_render_when_reasons_exist() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["신뢰도 높은 출처", "가격 / 비용 변화", "기업 도입"]
            )
        ]
    )

    assert "Key Signals: 신뢰도 높은 출처 · 가격 / 비용 변화 · 기업 도입" in message
    assert "•" not in message


def test_key_signals_hidden_when_reasons_are_empty() -> None:
    message = build_telegram_message([make_article(recommendation_reasons=[])])

    assert "Key Signals" not in message


def test_quality_pass_reason_is_never_rendered() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["저품질 패턴 없음", "신뢰도 높은 출처"]
            )
        ]
    )

    assert "저품질 패턴 없음" not in message
    assert "Key Signals: 신뢰도 높은 출처" in message


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

    assert "Key Signals: 신뢰도 높은 출처 · 가격 / 비용 변화 · 기업 도입" in message
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
    assert "Key Signals: 반도체 공급망" in message


def test_old_labels_are_absent() -> None:
    message = build_telegram_message([make_article()])

    assert "선정 포인트" not in message
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


def test_separator_is_not_rendered() -> None:
    message = build_telegram_message([make_article("First"), make_article("Second")])

    assert "────────────" not in message


def test_two_blank_lines_separate_article_cards() -> None:
    message = build_telegram_message([make_article("First"), make_article("Second")])

    first_link_end = '</a>'
    assert f"{first_link_end}\n\n\n✅ RECOMMENDED" in message


def test_no_blank_lines_inside_article_cards() -> None:
    message = build_telegram_message([make_article()])
    card = message.split("\n\n", 1)[1]

    assert "\n\n" not in card


def test_key_signals_multiple_reasons_use_middle_dot_separator() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["반도체 공급망", "투자 / IPO / M&A"]
            )
        ]
    )

    assert "Key Signals: 반도체 공급망 · 투자 / IPO / M&amp;A" in message


def test_link_uses_html_anchor_and_hides_visible_raw_url() -> None:
    message = build_telegram_message([make_article(url="https://example.com/article")])

    assert '🔗 <a href="https://example.com/article">Read</a>' in message
    assert "\nhttps://example.com/article" not in message


def test_link_url_is_html_attribute_escaped() -> None:
    message = build_telegram_message(
        [make_article(url='https://example.com/article?a=1&b="two"')]
    )

    assert 'href="https://example.com/article?a=1&amp;b=&quot;two&quot;"' in message
