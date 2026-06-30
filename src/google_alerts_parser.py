from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.models import Article
from src.url_normalizer import normalize_url


def parse_google_alerts_email(html: str) -> list[Article]:
    soup = BeautifulSoup(html or "", "html.parser")
    articles: list[Article] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a"):
        href = link.get("href")
        title = link.get_text(" ", strip=True)

        if not href or not title:
            continue

        if _is_skippable_link(href, title):
            continue

        normalized_url = normalize_url(href)
        if not normalized_url:
            continue

        if _is_skippable_link(normalized_url, title):
            continue

        if normalized_url in seen_urls:
            continue

        snippet = _extract_snippet(link)
        title, source = _split_title_and_source(title)
        seen_urls.add(normalized_url)
        articles.append(
            Article(title=title, source=source, url=normalized_url, snippet=snippet)
        )

    return articles


def _is_skippable_link(href: str, title: str) -> bool:
    href_lower = href.lower()
    title_lower = title.lower()

    skipped_href_parts = (
        "unsubscribe",
        "alerts.google.com",
        "myaccount.google.com",
        "accounts.google.com",
        "support.google.com",
        "google.com/alerts",
        "google.com/preferences",
        "google.com/settings",
        "google.com/notifications",
        "plus.google.com/share",
        "facebook.com/sharer",
        "twitter.com/share",
        "mailto:",
    )
    skipped_title_parts = (
        "unsubscribe",
        "flag as irrelevant",
        "edit this alert",
        "view all",
        "send feedback",
    )

    return (
        any(part in href_lower for part in skipped_href_parts)
        or any(part in title_lower for part in skipped_title_parts)
        or _is_url_text_only(title)
    )


def _is_url_text_only(text: str) -> bool:
    parsed = urlparse(text.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _split_title_and_source(text: str) -> tuple[str, str]:
    title, separator, source = text.rpartition(" - ")
    if not separator:
        return text, ""

    return title, source


def _extract_snippet(link) -> str:
    container = link.find_parent(attrs={"itemtype": "http://schema.org/Article"})
    if not container:
        return ""

    description = container.find(attrs={"itemprop": "description"})
    if not description:
        return ""

    return description.get_text(" ", strip=True)
