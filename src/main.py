from __future__ import annotations

import os

from src.curator import curate_articles
from src.dedup_store import DedupStore
from src.gmail_fetcher import fetch_recent_google_alerts_html
from src.google_alerts_parser import parse_google_alerts_email
from src.message_builder import build_telegram_message
from src.models import Article, CuratedArticle
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

    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_api_key:
        curated_articles = curate_articles(new_articles, openai_api_key)
    else:
        curated_articles = _build_fallback_curated_articles(new_articles)

    if not curated_articles:
        print("No high-signal articles selected.")
        return

    message = build_telegram_message(curated_articles)
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

    for article in curated_articles:
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


def _build_fallback_curated_articles(articles: list[Article]) -> list[CuratedArticle]:
    return [
        CuratedArticle(
            title=article.title,
            source=article.source,
            url=article.url,
            snippet=article.snippet,
            relevance_score=8,
            why_selected=(
                "Google Alerts에서 수집된 최근 기사입니다. "
                "AI/기술 트렌드 관련 키워드를 포함해 검토 후보로 선정했습니다."
            ),
            korean_summary=(
                "OpenAI API가 연결되지 않아 본문 요약은 생성하지 않았습니다. "
                "원문 제목과 링크를 확인하세요."
            ),
            career_market_insight=(
                "자동 인사이트는 비활성화 상태입니다. "
                "OpenAI API 연결 후 개인 관심사 기반 커리어/시장 해석이 생성됩니다."
            ),
        )
        for article in articles[:3]
    ]


if __name__ == "__main__":
    main()
