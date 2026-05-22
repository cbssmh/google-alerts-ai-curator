from src.models import Article
from src.rule_based_selector import select_high_signal_articles


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
    assert "이 흐름은 AI 시장의 경쟁 구도와 기술 채택 방향" in selected[0].why_selected
    assert "생태계 주도권" in selected[0].career_market_insight


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
