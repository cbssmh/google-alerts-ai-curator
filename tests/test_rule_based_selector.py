from src.models import Article
from src.rule_based_selector import score_to_stars, select_high_signal_articles


def make_article(
    title: str,
    source: str = "",
    url: str = "https://example.com/article",
    snippet: str = "",
) -> Article:
    return Article(title=title, source=source, url=url, snippet=snippet)


def test_credible_source_increases_score() -> None:
    articles = [
        make_article("Enterprise AI agent adoption grows", source="Reuters"),
        make_article("Enterprise AI agent adoption grows", source="Unknown Blog"),
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert selected[0].source == "Reuters"
    assert selected[0].relevance_score == 7
    assert "신뢰도 높은 출처" in selected[0].recommendation_reasons


def test_trusted_source_reason_requires_article_source_match() -> None:
    articles = [
        make_article(
            "OpenAI cuts API pricing for developers",
            source="Unknown Blog",
            snippet="Reuters reported that the change affects inference cost.",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "신뢰도 높은 출처" not in selected[0].recommendation_reasons


def test_official_release_reason() -> None:
    articles = [
        make_article(
            "OpenAI releases new API preview",
            source="OpenAI Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "공식 발표" in selected[0].recommendation_reasons


def test_pricing_cost_reason() -> None:
    articles = [
        make_article(
            "OpenAI cuts API pricing as inference cost gets cheaper",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "가격 / 비용 변화" in selected[0].recommendation_reasons


def test_infrastructure_investment_reason() -> None:
    articles = [
        make_article(
            "AI data center capex and power grid spending accelerates",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "인프라 투자" in selected[0].recommendation_reasons


def test_generic_spending_alone_does_not_create_infrastructure_reason() -> None:
    articles = [
        make_article(
            "Where does federal AI spending stand in 2026",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "인프라 투자" not in selected[0].recommendation_reasons


def test_semiconductor_supply_chain_reason() -> None:
    articles = [
        make_article(
            "HBM packaging yield constrains GPU supply chain",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "반도체 공급망" in selected[0].recommendation_reasons


def test_government_regulation_reason() -> None:
    articles = [
        make_article(
            "FTC opens antitrust policy probe into AI market",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "정부 / 규제" in selected[0].recommendation_reasons


def test_developer_ecosystem_reason() -> None:
    articles = [
        make_article(
            "Anthropic publishes SDK documentation and GitHub release notes",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "개발자 생태계" in selected[0].recommendation_reasons


def test_generic_developer_alone_does_not_create_developer_ecosystem_reason() -> None:
    articles = [
        make_article(
            "Google developer conference focuses on AI demos",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "개발자 생태계" not in selected[0].recommendation_reasons


def test_enterprise_adoption_reason() -> None:
    articles = [
        make_article(
            "Enterprise customer deployment expands Copilot workflow adoption",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "기업 도입" in selected[0].recommendation_reasons


def test_security_incident_reason() -> None:
    articles = [
        make_article(
            "AI platform vulnerability exposes customer data",
            source="Unknown Blog",
            snippet="Researchers disclosed a security flaw and CVE.",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "보안 사고" in selected[0].recommendation_reasons


def test_funding_ipo_ma_reason() -> None:
    articles = [
        make_article(
            "Cerebras IPO market debut follows new funding valuation",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "투자 / IPO / M&A" in selected[0].recommendation_reasons


def test_product_platform_strategy_reason() -> None:
    articles = [
        make_article(
            "Google makes Gemini the default integration across Search",
            source="Unknown Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "제품 / 플랫폼 전략" in selected[0].recommendation_reasons


def test_generic_platform_alone_does_not_create_product_platform_reason() -> None:
    articles = [
        make_article(
            "AI platform startup expands enterprise workflow",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "제품 / 플랫폼 전략" not in selected[0].recommendation_reasons


def test_quality_pass_reason_is_not_user_facing() -> None:
    articles = [
        make_article(
            "Enterprise Copilot productivity rollout",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "저품질 패턴 없음" not in selected[0].recommendation_reasons


def test_recommendation_reasons_do_not_expose_internal_labels() -> None:
    articles = [
        make_article(
            "Google shifts AI search and browser interface",
            source="TIME",
        )
    ]

    selected = select_high_signal_articles(articles)
    reasons_text = " ".join(selected[0].recommendation_reasons)

    assert "platform_shift" not in reasons_text
    assert "ecosystem_competition" not in reasons_text
    assert "interface_shift" not in reasons_text
    assert "semiconductor" not in reasons_text
    assert "Platform Shift" not in reasons_text
    assert "Ecosystem Competition" not in reasons_text
    assert "AI Interface Shift" not in reasons_text
    assert "Semiconductor Race" not in reasons_text


def test_recommendation_reasons_are_capped_to_3() -> None:
    articles = [
        make_article(
            "OpenAI releases API pricing for enterprise data center GPU platform IPO",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected[0].recommendation_reasons) == 3


def test_low_value_stock_pumping_article_is_not_selected() -> None:
    articles = [
        make_article(
            "AI penny stock to buy surges after shocking price target",
            source="Unknown Blog",
        )
    ]

    assert select_high_signal_articles(articles) == []


def test_question_headline_before_source_suffix_is_penalized() -> None:
    articles = [
        make_article(
            "Where does AI data center spending stand in 2026 ? | Example",
            source="Reuters",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "인프라 투자" in selected[0].recommendation_reasons
    assert "저품질 패턴 없음" not in selected[0].recommendation_reasons


def test_low_value_article_is_filtered_out() -> None:
    articles = [
        make_article("Top 10 celebrity AI memes that went viral", source="Unknown Blog")
    ]

    assert select_high_signal_articles(articles) == []


def test_high_signal_infrastructure_article_is_selected() -> None:
    articles = [
        make_article(
            "Nvidia GPU demand drives new data center buildout",
            source="NVIDIA Blog",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert selected[0].relevance_score >= 5
    assert "AI Infrastructure" in selected[0].why_selected
    assert "데이터센터" in selected[0].career_market_insight


def test_generic_jobs_fear_article_is_not_prioritized() -> None:
    articles = [
        make_article(
            "AI will take your job and trigger jobs panic",
            source="Reuters",
        )
    ]

    assert select_high_signal_articles(articles) == []


def test_platform_shift_explains_why_the_trend_matters() -> None:
    articles = [
        make_article(
            "OpenAI launches new developer platform and app store ecosystem",
            source="The Information",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "Platform Shift" in selected[0].why_selected
    assert "주요 신호: Ecosystem Competition" in selected[0].why_selected
    assert "제품 생태계와 유통 채널 경쟁" in selected[0].why_selected
    assert "협력과 수익 배분 구조" in selected[0].career_market_insight


def test_interface_shift_article_is_selected() -> None:
    articles = [
        make_article(
            "Google changes search and browser interface with AI assistant",
            source="The Verge",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "AI Interface Shift" in selected[0].why_selected


def test_results_are_sorted_by_score_descending() -> None:
    articles = [
        make_article("Enterprise Copilot productivity rollout", source="TechCrunch"),
        make_article(
            "Nvidia GPU and semiconductor supply reshape cloud infrastructure",
            source="Bloomberg",
        ),
    ]

    selected = select_high_signal_articles(articles)

    assert selected[0].title.startswith("Nvidia GPU")
    assert selected[0].relevance_score > selected[1].relevance_score


def test_limit_3() -> None:
    articles = [
        make_article(f"Enterprise agent productivity rollout {index}", source="Reuters")
        for index in range(4)
    ]

    selected = select_high_signal_articles(articles, limit=3)

    assert len(selected) == 3


def test_google_shifts_to_ai_search_is_selected() -> None:
    articles = [
        make_article(
            "Google Shifts to AI Search, Heralding Major Change in How People Use the Internet",
            source="TIME",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "AI Interface Shift" in selected[0].why_selected


def test_why_selected_includes_snippet_evidence_when_present() -> None:
    articles = [
        make_article(
            "Google is dethroning OpenAI as the king of consumer AI",
            source="The Economist",
            snippet=(
                "Google is using distribution through Android, Search, and Gemini "
                "to challenge OpenAI in consumer AI products."
            ),
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "알림 요약 근거" in selected[0].why_selected
    assert "Android, Search, and Gemini" in selected[0].why_selected
    assert "Ecosystem Competition" in selected[0].why_selected


def test_why_selected_falls_back_to_title_when_snippet_is_empty() -> None:
    articles = [
        make_article(
            "Google is dethroning OpenAI as the king of consumer AI",
            source="The Economist",
            snippet="",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "제목 근거" in selected[0].why_selected
    assert "Google is dethroning OpenAI" in selected[0].why_selected


def test_matched_signal_labels_are_unique() -> None:
    articles = [
        make_article(
            "Google Shifts to AI Search with a new search interface",
            source="TIME",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert selected[0].why_selected.count("AI Interface Shift") == 1


def test_white_house_ai_order_is_selected() -> None:
    articles = [
        make_article(
            "AI & Tech Brief: Exclusive | White House AI order expected",
            source="The Washington Post",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "Government / Regulation" in selected[0].why_selected


def test_dethroning_openai_article_is_selected() -> None:
    articles = [
        make_article(
            "Google is dethroning OpenAI as the king of consumer AI",
            source="The Economist",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert len(selected) == 1
    assert "Ecosystem Competition" in selected[0].why_selected


def test_generic_graduation_booing_does_not_outrank_market_shift_articles() -> None:
    articles = [
        make_article(
            "Students boo AI speaker at graduation ceremony",
            source="Unknown Blog",
        ),
        make_article(
            "Google Shifts to AI Search, Heralding Major Change in How People Use the Internet",
            source="TIME",
        ),
        make_article(
            "AI & Tech Brief: Exclusive | White House AI order expected",
            source="The Washington Post",
        ),
    ]

    selected = select_high_signal_articles(articles)

    assert all("graduation" not in article.title.lower() for article in selected)
    assert selected[0].title.startswith("AI & Tech Brief") or selected[0].title.startswith("Google Shifts")


def test_career_market_insight_follows_primary_matched_signal() -> None:
    articles = [
        make_article(
            "Google Shifts to AI Search, Heralding Major Change in How People Use the Internet",
            source="TIME",
            snippet="Google also mentioned AI infrastructure and chips spending.",
        )
    ]

    selected = select_high_signal_articles(articles)

    assert "AI Interface Shift" in selected[0].why_selected
    assert "검색, 브라우저, 어시스턴트" in selected[0].career_market_insight
    assert "반도체 경쟁" not in selected[0].career_market_insight


def test_existing_ranking_and_threshold_behavior_remains_stable() -> None:
    articles = [
        make_article("Top 10 celebrity AI memes that went viral", source="Unknown Blog"),
        make_article("Enterprise Copilot productivity rollout", source="TechCrunch"),
        make_article(
            "Nvidia GPU and semiconductor supply reshape cloud infrastructure",
            source="Bloomberg",
        ),
    ]

    selected = select_high_signal_articles(articles)

    assert [article.title for article in selected] == [
        "Nvidia GPU and semiconductor supply reshape cloud infrastructure",
        "Enterprise Copilot productivity rollout",
    ]


def test_score_to_stars_maps_selected_score_ranges() -> None:
    assert score_to_stars(12) == "⭐⭐⭐⭐⭐"
    assert score_to_stars(8) == "⭐⭐⭐⭐☆"
    assert score_to_stars(4) == "⭐⭐⭐☆☆"
