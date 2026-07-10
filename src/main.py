from __future__ import annotations

import os

from src.config import get_llm_provider_config
from src.dedup_store import DedupStore
from src.gmail_fetcher import fetch_recent_google_alerts_html
from src.google_alerts_parser import parse_google_alerts_email
from src.message_enhancer import enhance_message_with_llm
from src.message_builder import build_telegram_message
from src.rule_based_selector import select_high_signal_articles
from src.telegram_sender import send_telegram_message


REQUIRED_ENV_VARS = (
    "GMAIL_EMAIL",
    "GMAIL_APP_PASSWORD",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)


def main() -> None:
    env = _load_required_env()
    if env is None:
        return

    html_emails = fetch_recent_google_alerts_html(
        env["GMAIL_EMAIL"],
        env["GMAIL_APP_PASSWORD"],
    )
    if not html_emails:
        print("No recent Google Alerts emails found.")
        return

    articles = []
    for html in html_emails:
        articles.extend(parse_google_alerts_email(html))

    if not articles:
        print("No articles parsed from Google Alerts emails.")
        return

    dedup_store = DedupStore()
    new_articles = dedup_store.filter_new_articles(articles)
    if not new_articles:
        print("No new articles to process.")
        return

    curated_articles = select_high_signal_articles(new_articles)
    articles_to_mark_processed = curated_articles
    message_header = "Daily High-Signal Tech Alerts"
    show_summary = False
    daily_trends = []

    llm_config = get_llm_provider_config()
    if llm_config and curated_articles:
        curated_articles, daily_trends = enhance_message_with_llm(
            curated_articles,
            llm_config.api_key,
            model=llm_config.model,
            base_url=llm_config.base_url,
            timeout_seconds=llm_config.timeout_seconds,
        )
        show_summary = True

    if not curated_articles:
        print("No high-signal articles selected.")
        return

    message = build_telegram_message(
        curated_articles,
        header=message_header,
        show_summary=show_summary,
        daily_trends=daily_trends,
    )
    if not message:
        print("No Telegram message generated.")
        return

    sent = send_telegram_message(
        env["TELEGRAM_BOT_TOKEN"],
        env["TELEGRAM_CHAT_ID"],
        message,
    )
    if not sent:
        print("Telegram send failed.")
        return

    for article in articles_to_mark_processed:
        dedup_store.mark_processed(article.url)
    dedup_store.save()
    print(f"Sent {len(curated_articles)} curated articles.")


def _load_required_env() -> dict[str, str] | None:
    env = {name: os.environ.get(name, "") for name in REQUIRED_ENV_VARS}
    missing = [name for name, value in env.items() if not value]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return None

    return env


if __name__ == "__main__":
    main()
