from src.models import CuratedArticle


def build_telegram_message(
    articles: list[CuratedArticle],
    header: str = "Daily AI Curated News Top 3",
    show_summary: bool = True,
) -> str:
    if not articles:
        return ""

    sections = [header]
    for index, article in enumerate(articles, start=1):
        lines = [
            f"{index}. {article.title}",
            f"출처: {article.source}",
            f"링크: {article.url}",
            f"관련도 점수: {article.relevance_score}",
            f"선정 이유: {article.why_selected}",
        ]
        if show_summary:
            lines.append(f"요약: {article.korean_summary}")
        lines.append(f"커리어 / 시장 인사이트: {article.career_market_insight}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)
