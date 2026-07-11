from src.message_builder import build_telegram_message
from src.models import CuratedArticle, DailyLandscape, TrendTheme


def make_article(
    title: str = "Original AI Title",
    source: str = "Example",
    relevance_score: int = 9,
    recommendation_reasons=None,
    url: str = "https://example.com/article",
    korean_title: str = "",
    preview: str = "",
    enhanced_why_selected: str = "",
    confidence: str = "",
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
        korean_title=korean_title,
        preview=preview,
        enhanced_why_selected=enhanced_why_selected,
        confidence=confidence,
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


def test_why_selected_renders_when_reasons_exist() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["신뢰도 높은 출처", "가격 / 비용 변화", "기업 도입"]
            )
        ]
    )

    assert "✓ Why selected\n신뢰도 높은 출처 · 가격 / 비용 변화 · 기업 도입" in message
    assert "Key Signals" not in message


def test_why_selected_hidden_when_reasons_are_empty() -> None:
    message = build_telegram_message([make_article(recommendation_reasons=[])])

    assert "✓ Why selected" not in message
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
    assert "✓ Why selected\n신뢰도 높은 출처" in message


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

    assert "✓ Why selected\n신뢰도 높은 출처 · 가격 / 비용 변화 · 기업 도입" in message
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
    assert "✓ Why selected\n반도체 공급망" in message


def test_old_labels_are_absent() -> None:
    message = build_telegram_message([make_article()])

    assert "선정 포인트" not in message
    assert "Key Signals" not in message
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


def test_separator_is_rendered_between_cards() -> None:
    message = build_telegram_message([make_article("First"), make_article("Second")])

    assert "━━━━━━━━━━━━━━" in message


def test_separator_separates_article_cards() -> None:
    message = build_telegram_message([make_article("First"), make_article("Second")])

    first_link_end = '</a>'
    assert f"{first_link_end}\n\n━━━━━━━━━━━━━━\n\n✅ RECOMMENDED" in message


def test_why_selected_multiple_reasons_use_middle_dot_separator() -> None:
    message = build_telegram_message(
        [
            make_article(
                recommendation_reasons=["반도체 공급망", "투자 / IPO / M&A"]
            )
        ]
    )

    assert "✓ Why selected\n반도체 공급망 · 투자 / IPO / M&amp;A" in message


def test_link_uses_html_anchor_and_hides_visible_raw_url() -> None:
    message = build_telegram_message([make_article(url="https://example.com/article")])

    assert '🔗 <a href="https://example.com/article">Read →</a>' in message
    assert "\nhttps://example.com/article" not in message


def test_link_label_is_stable_when_source_is_empty() -> None:
    message = build_telegram_message(
        [make_article(source=" ", url="https://example.com/article")]
    )

    assert '🔗 <a href="https://example.com/article">Read →</a>' in message
    assert "Read on" not in message


def test_enhanced_korean_title_and_preview_render() -> None:
    message = build_telegram_message(
        [
            make_article(
                korean_title="AI 반도체 투자 확대",
                preview="AI 반도체 투자 확대를 다룬 기사입니다.",
                confidence="high",
            )
        ]
    )

    assert "🇰🇷 AI 반도체 투자 확대" in message
    assert "AI 반도체 투자 확대를 다룬 기사입니다." in message


def test_low_confidence_preview_is_hidden() -> None:
    message = build_telegram_message(
        [
            make_article(
                preview="AI 반도체 투자 확대를 다룬 기사입니다.",
                confidence="low",
            )
        ]
    )

    assert "AI 반도체 투자 확대를 다룬 기사입니다." not in message


def test_enhanced_why_selected_takes_priority() -> None:
    message = build_telegram_message(
        [
            make_article(
                enhanced_why_selected="반도체 공급망 변화가 핵심인 기사입니다.",
                recommendation_reasons=["신뢰도 높은 출처"],
            )
        ]
    )

    assert "반도체 공급망 변화가 핵심인 기사입니다." in message
    assert "신뢰도 높은 출처" not in message


def test_daily_trends_render_above_cards() -> None:
    message = build_telegram_message(
        [make_article()],
        daily_trends=["AI 인프라 투자 확대", "모델 가격 경쟁 심화"],
    )

    assert message.startswith("📰 오늘의 AI 흐름")
    assert "• AI 인프라 투자 확대" in message
    assert "• 모델 가격 경쟁 심화" in message
    assert "Daily High-Signal Tech Alerts" not in message


def test_landscape_headline_renders_above_cards() -> None:
    message = build_telegram_message(
        [make_article()],
        landscape=DailyLandscape(
            headline="AI 인프라 투자와 기업 AI 관련 소식이 함께 나타났습니다."
        ),
    )

    assert message.startswith("📰 오늘의 AI Landscape")
    assert "AI 인프라 투자와 기업 AI 관련 소식이 함께 나타났습니다." in message
    assert "Daily High-Signal Tech Alerts" not in message
    assert "━━━━━━━━━━━━━━" in message


def test_landscape_empty_matches_existing_header_behavior() -> None:
    baseline = build_telegram_message([make_article()])
    with_empty_landscape = build_telegram_message(
        [make_article()],
        landscape=DailyLandscape(),
    )

    assert with_empty_landscape == baseline


def test_landscape_sections_hide_empty_fields() -> None:
    message = build_telegram_message(
        [make_article()],
        landscape=DailyLandscape(
            themes=[TrendTheme(label="AI 인프라 투자", article_indices=[0, 1])],
        ),
    )

    assert "주요 흐름" in message
    assert "• AI 인프라 투자" in message
    assert "주요 키워드" not in message
    assert "주요 기업·기관" not in message


def test_landscape_keywords_and_entities_render_compactly() -> None:
    message = build_telegram_message(
        [make_article()],
        landscape=DailyLandscape(
            keywords=["HBM", "GPU", "Inference"],
            entities=["NVIDIA", "OpenAI", "Samsung"],
        ),
    )

    assert "주요 키워드\nHBM · GPU · Inference" in message
    assert "주요 기업·기관\nNVIDIA · OpenAI · Samsung" in message


def test_landscape_text_is_html_escaped() -> None:
    message = build_telegram_message(
        [make_article()],
        landscape=DailyLandscape(
            headline="OpenAI & Google <AI>",
            themes=[TrendTheme(label="GPU & HBM <supply>", article_indices=[0, 1])],
            keywords=["API <pricing>"],
            entities=["NVIDIA & OpenAI"],
        ),
    )

    assert "OpenAI &amp; Google &lt;AI&gt;" in message
    assert "GPU &amp; HBM &lt;supply&gt;" in message
    assert "API &lt;pricing&gt;" in message
    assert "NVIDIA &amp; OpenAI" in message


def test_link_url_is_html_attribute_escaped() -> None:
    message = build_telegram_message(
        [make_article(url='https://example.com/article?a=1&b="two"')]
    )

    assert 'href="https://example.com/article?a=1&amp;b=&quot;two&quot;"' in message
