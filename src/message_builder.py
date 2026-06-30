from src.models import CuratedArticle
from src.rule_based_selector import score_to_stars


CIRCLED_NUMBERS = {
    1: "①",
    2: "②",
    3: "③",
}

INTERNAL_REASON_LABELS = {
    "저품질 패턴 없음",
    "platform_shift",
    "ecosystem_competition",
    "interface_shift",
    "semiconductor",
    "Platform Shift",
    "Ecosystem Competition",
    "AI Interface Shift",
    "Semiconductor Race",
}

SEPARATOR = "────────────"


def build_telegram_message(
    articles: list[CuratedArticle],
    header: str = "Daily High-Signal Tech Alerts",
    show_summary: bool = True,
) -> str:
    if not articles:
        return ""

    article_sections = [
        _build_article_section(index, article)
        for index, article in enumerate(articles, start=1)
    ]
    return header + "\n\n" + f"\n\n{SEPARATOR}\n\n".join(article_sections)


def _build_article_section(index: int, article: CuratedArticle) -> str:
    lines = [
        f"{_rank_label(index)} {score_to_stars(article.relevance_score)}",
        "",
        _clean_text(article.title),
    ]

    source = _clean_text(article.source)
    if source:
        lines.append(source)

    reasons = _reader_facing_reasons(article.recommendation_reasons)
    if reasons:
        lines.extend(["", "선정 포인트"])
        lines.extend(f"• {reason}" for reason in reasons)

    lines.extend(["", "🔗 Read", article.url])
    return "\n".join(lines)


def _rank_label(index: int) -> str:
    return CIRCLED_NUMBERS.get(index, f"{index}.")


def _reader_facing_reasons(reasons: list[str], limit: int = 3) -> list[str]:
    reader_facing = []
    for reason in reasons:
        cleaned = _clean_text(reason)
        if not cleaned or cleaned in INTERNAL_REASON_LABELS:
            continue

        if cleaned not in reader_facing:
            reader_facing.append(cleaned)

        if len(reader_facing) == limit:
            break

    return reader_facing


def _clean_text(text: str) -> str:
    return " ".join(text.split())
