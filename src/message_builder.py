from src.models import CuratedArticle


def build_telegram_message(articles: list[CuratedArticle]) -> str:
    if not articles:
        return ""

    sections = ["Daily AI Curated News Top 3"]
    for index, article in enumerate(articles, start=1):
        sections.append(
            "\n".join(
                [
                    f"{index}. {article.title}",
                    f"Source: {article.source}",
                    f"Link: {article.url}",
                    f"Relevance score: {article.relevance_score}",
                    f"Why selected: {article.why_selected}",
                    f"Korean summary: {article.korean_summary}",
                    f"Career / market insight: {article.career_market_insight}",
                ]
            )
        )

    return "\n\n".join(sections)
