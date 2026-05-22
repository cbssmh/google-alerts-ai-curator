from src import main as main_module
from src.models import Article, CuratedArticle


def set_required_env(monkeypatch) -> None:
    monkeypatch.setenv("GMAIL_EMAIL", "user@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-id")


def make_article(url: str = "https://example.com/article") -> Article:
    return Article(title="Article", source="", url=url, snippet="")


def make_curated_article(url: str = "https://example.com/article") -> CuratedArticle:
    return CuratedArticle(
        title="Article",
        source="Example",
        url=url,
        snippet="",
        relevance_score=9,
        why_selected="선정 이유",
        korean_summary="한국어 요약",
        career_market_insight="커리어 인사이트",
    )


class FakeDedupStore:
    def __init__(self):
        self.marked_urls = []
        self.saved = False
        self.new_articles = []

    def filter_new_articles(self, articles):
        return self.new_articles

    def mark_processed(self, url):
        self.marked_urls.append(url)

    def save(self):
        self.saved = True


def test_no_html_emails_exits_without_error(monkeypatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.setattr(main_module, "fetch_recent_google_alerts_html", lambda *args: [])

    main_module.main()


def test_no_new_articles_exits_without_sending_telegram(monkeypatch) -> None:
    set_required_env(monkeypatch)
    store = FakeDedupStore()
    monkeypatch.setattr(main_module, "DedupStore", lambda: store)
    monkeypatch.setattr(
        main_module,
        "fetch_recent_google_alerts_html",
        lambda *args: ["<html></html>"],
    )
    monkeypatch.setattr(
        main_module,
        "parse_google_alerts_email",
        lambda html: [make_article()],
    )

    sent = False

    def fake_send(*args):
        nonlocal sent
        sent = True
        return True

    monkeypatch.setattr(main_module, "send_telegram_message", fake_send)

    main_module.main()

    assert sent is False


def test_successful_pipeline_sends_telegram_and_saves_dedup(monkeypatch) -> None:
    set_required_env(monkeypatch)
    article = make_article()
    curated_article = make_curated_article()
    store = FakeDedupStore()
    store.new_articles = [article]
    monkeypatch.setattr(main_module, "DedupStore", lambda: store)
    monkeypatch.setattr(
        main_module,
        "fetch_recent_google_alerts_html",
        lambda *args: ["<html></html>"],
    )
    monkeypatch.setattr(main_module, "parse_google_alerts_email", lambda html: [article])
    monkeypatch.setattr(
        main_module,
        "curate_articles",
        lambda articles, api_key: [curated_article],
    )
    monkeypatch.setattr(
        main_module,
        "build_telegram_message",
        lambda articles: "telegram message",
    )

    sent_messages = []

    def fake_send(bot_token, chat_id, message):
        sent_messages.append(message)
        return True

    monkeypatch.setattr(main_module, "send_telegram_message", fake_send)

    main_module.main()

    assert sent_messages == ["telegram message"]
    assert store.marked_urls == [curated_article.url]
    assert store.saved is True


def test_failed_telegram_send_does_not_mark_processed_urls(monkeypatch) -> None:
    set_required_env(monkeypatch)
    article = make_article()
    curated_article = make_curated_article()
    store = FakeDedupStore()
    store.new_articles = [article]
    monkeypatch.setattr(main_module, "DedupStore", lambda: store)
    monkeypatch.setattr(
        main_module,
        "fetch_recent_google_alerts_html",
        lambda *args: ["<html></html>"],
    )
    monkeypatch.setattr(main_module, "parse_google_alerts_email", lambda html: [article])
    monkeypatch.setattr(
        main_module,
        "curate_articles",
        lambda articles, api_key: [curated_article],
    )
    monkeypatch.setattr(
        main_module,
        "build_telegram_message",
        lambda articles: "telegram message",
    )
    monkeypatch.setattr(main_module, "send_telegram_message", lambda *args: False)

    main_module.main()

    assert store.marked_urls == []
    assert store.saved is False


def test_missing_openai_api_key_uses_fallback_mode(monkeypatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY")
    articles = [
        make_article("https://example.com/one"),
        make_article("https://example.com/two"),
        make_article("https://example.com/three"),
        make_article("https://example.com/four"),
    ]
    store = FakeDedupStore()
    store.new_articles = articles
    monkeypatch.setattr(main_module, "DedupStore", lambda: store)
    monkeypatch.setattr(
        main_module,
        "fetch_recent_google_alerts_html",
        lambda *args: ["<html></html>"],
    )
    monkeypatch.setattr(main_module, "parse_google_alerts_email", lambda html: articles)

    openai_called = False

    def fake_curate_articles(new_articles, api_key):
        nonlocal openai_called
        openai_called = True
        return []

    monkeypatch.setattr(main_module, "curate_articles", fake_curate_articles)

    built_articles = []

    def fake_build_telegram_message(curated_articles):
        built_articles.extend(curated_articles)
        return "telegram message"

    monkeypatch.setattr(
        main_module,
        "build_telegram_message",
        fake_build_telegram_message,
    )
    monkeypatch.setattr(main_module, "send_telegram_message", lambda *args: True)

    main_module.main()

    assert openai_called is False
    assert len(built_articles) == 3
    assert built_articles[0].relevance_score == 8
    assert "Fallback mode" not in built_articles[0].why_selected
    assert built_articles[0].korean_summary != articles[0].title
    assert built_articles[0].career_market_insight
    assert store.marked_urls == [article.url for article in built_articles]
    assert store.saved is True
