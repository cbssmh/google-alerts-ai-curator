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

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)
        articles.append(Article(title=title, source="", url=normalized_url, snippet=""))

    return articles


def _is_skippable_link(href: str, title: str) -> bool:
    href_lower = href.lower()
    title_lower = title.lower()

    skipped_href_parts = (
        "unsubscribe",
        "alerts.google.com",
        "google.com/alerts",
        "google.com/preferences",
        "google.com/settings",
        "accounts.google.com",
        "support.google.com",
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

    return any(part in href_lower for part in skipped_href_parts) or any(
        part in title_lower for part in skipped_title_parts
    )
