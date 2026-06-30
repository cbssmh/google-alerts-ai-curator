import re

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
            f"📰 {_clean_text(article.title)}",
        ]

        source = _clean_text(article.source)
        if source:
            lines.extend(["", f"📂 {source}"])

        snippet = _clean_snippet(article.snippet)
        if snippet:
            lines.extend(["", "📝 Google Alerts", snippet])

        why_lines = [_reader_facing_why(article.why_selected)]
        evidence = _short_evidence(article.snippet)
        if evidence:
            why_lines.extend(["", f"근거: {evidence}"])

        lines.extend(
            [
                "",
                "💡 Why it Matters",
                "\n".join(why_lines),
                "",
                "🔗 Read",
                article.url,
            ]
        )

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _clean_snippet(text: str) -> str:
    cleaned = _clean_text(text)
    cleaned = re.sub(r"\s+([,.;:?!%)\]}])", r"\1", cleaned)
    cleaned = re.sub(r"([(\[{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+-\s*", "-", cleaned)
    return cleaned


def _short_evidence(text: str, max_length: int = 150) -> str:
    cleaned = _clean_snippet(text)
    if not cleaned:
        return ""

    if len(cleaned) <= max_length:
        return cleaned

    return cleaned[: max_length - 3].rstrip(" ,.;:") + "..."


def _reader_facing_why(why_selected: str) -> str:
    cleaned = _clean_text(why_selected)
    marker = "이는 "
    marker_index = cleaned.rfind(marker)
    if marker_index != -1:
        return cleaned[marker_index:]

    return cleaned
