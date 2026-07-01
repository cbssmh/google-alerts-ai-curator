from html import escape

from src.models import CuratedArticle

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
    return _escape_text(header) + "\n\n" + "\n\n\n".join(article_sections)


def _build_article_section(index: int, article: CuratedArticle) -> str:
    lines = [
        _recommendation_tier(article.relevance_score),
        _escape_text(_clean_text(article.title)),
    ]

    reasons = _reader_facing_reasons(article.recommendation_reasons)
    if reasons:
        signals = " · ".join(_escape_text(reason) for reason in reasons)
        lines.append(f"Key Signals: {signals}")

    lines.append(
        f'🔗 <a href="{_escape_attr(article.url)}">{_read_link_label(article.source)}</a>'
    )
    return "\n".join(lines)


def _recommendation_tier(score: int) -> str:
    if score >= 20:
        return "🏆 ESSENTIAL"

    if score >= 8:
        return "✅ RECOMMENDED"

    return "👀 WORTH A LOOK"


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


def _read_link_label(source: str) -> str:
    cleaned_source = _clean_text(source)
    if not cleaned_source:
        return "Read"

    return f"Read on {_escape_text(cleaned_source)}"


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _escape_text(text: str) -> str:
    return escape(text, quote=False)


def _escape_attr(text: str) -> str:
    return escape(text, quote=True)
