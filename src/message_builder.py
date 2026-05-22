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
                    f"출처: {article.source}",
                    f"링크: {article.url}",
                    f"관련도 점수: {article.relevance_score}",
                    f"선정 이유: {article.why_selected}",
                    f"요약: {article.korean_summary}",
                    f"커리어 / 시장 인사이트: {article.career_market_insight}",
                ]
            )
        )

    return "\n\n".join(sections)
