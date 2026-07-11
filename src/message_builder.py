from __future__ import annotations

from html import escape

from src.models import CuratedArticle, DailyLandscape

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
    daily_trends: list[str] | None = None,
    landscape: DailyLandscape | None = None,
) -> str:
    if not articles:
        return ""

    article_sections = [
        _build_article_section(index, article)
        for index, article in enumerate(articles, start=1)
    ]
    sections = []
    landscape_section = _build_landscape_section(landscape)
    if landscape_section:
        sections.append(landscape_section)
    else:
        trend_section = _build_daily_trends_section(daily_trends or [])
        if trend_section:
            sections.append(trend_section)
        else:
            sections.append(_escape_text(header))

    sections.extend(article_sections)
    return "\n\n━━━━━━━━━━━━━━\n\n".join(sections)


def _build_article_section(index: int, article: CuratedArticle) -> str:
    lines = [
        _recommendation_tier(article.relevance_score),
        _escape_text(_clean_text(article.title)),
    ]

    korean_title = _clean_text(article.korean_title)
    if korean_title:
        lines.extend(["", f"🇰🇷 {_escape_text(korean_title)}"])

    preview = _clean_text(article.preview)
    if preview and article.confidence.lower() != "low":
        lines.extend(["", _escape_text(preview)])

    why_selected = _clean_text(article.enhanced_why_selected)
    if not why_selected:
        reasons = _reader_facing_reasons(article.recommendation_reasons)
        why_selected = " · ".join(reasons)

    if why_selected:
        lines.extend(["", "✓ Why selected", _escape_text(why_selected)])

    lines.append(
        f'🔗 <a href="{_escape_attr(article.url)}">Read →</a>'
    )
    return "\n".join(lines)


def _build_daily_trends_section(daily_trends: list[str]) -> str:
    cleaned_trends = []
    for trend in daily_trends:
        cleaned = _clean_text(trend)
        if cleaned and cleaned not in cleaned_trends:
            cleaned_trends.append(cleaned)

        if len(cleaned_trends) == 3:
            break

    if not cleaned_trends:
        return ""

    lines = ["📰 오늘의 AI 흐름", ""]
    lines.extend(f"• {_escape_text(trend)}" for trend in cleaned_trends)
    return "\n".join(lines)


def _build_landscape_section(landscape: DailyLandscape | None) -> str:
    if landscape is None or landscape.is_empty():
        return ""

    lines = ["📰 오늘의 AI Landscape"]
    headline = _clean_text(landscape.headline)
    if headline:
        lines.extend(["", _escape_text(headline)])

    theme_labels = []
    for theme in landscape.themes:
        label = _clean_text(theme.label)
        if label and label not in theme_labels:
            theme_labels.append(label)

    if theme_labels:
        lines.extend(["", "주요 흐름"])
        lines.extend(f"• {_escape_text(label)}" for label in theme_labels)

    keywords = _clean_unique_terms(landscape.keywords, limit=6)
    if keywords:
        lines.extend(["", "주요 키워드", _escape_text(" · ".join(keywords))])

    entities = _clean_unique_terms(landscape.entities, limit=5)
    if entities:
        lines.extend(["", "주요 기업·기관", _escape_text(" · ".join(entities))])

    return "\n".join(lines)


def _clean_unique_terms(terms: list[str], limit: int) -> list[str]:
    cleaned_terms = []
    for term in terms:
        cleaned = _clean_text(term)
        if cleaned and cleaned not in cleaned_terms:
            cleaned_terms.append(cleaned)

        if len(cleaned_terms) == limit:
            break

    return cleaned_terms


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


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _escape_text(text: str) -> str:
    return escape(text, quote=False)


def _escape_attr(text: str) -> str:
    return escape(text, quote=True)
