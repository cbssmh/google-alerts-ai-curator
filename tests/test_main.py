from src import main as main_module
from src.models import Article, CuratedArticle, DailyLandscape, TrendTheme


def set_required_env(monkeypatch) -> None:
    monkeypatch.setenv("GMAIL_EMAIL", "user@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
    monkeypatch.setenv("LLM_PROVIDER", "off")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-id")


def make_article(
    url: str = "https://example.com/article",
    title: str = "Nvidia GPU demand lifts cloud infrastructure spending",
    source: str = "Reuters",
    snippet: str = "Nvidia GPU demand is increasing cloud infrastructure spending.",
) -> Article:
    return Article(title=title, source=source, url=url, snippet=snippet)


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
        "build_telegram_message",
        lambda articles, header="Daily High-Signal Tech Alerts", show_summary=False, daily_trends=None, landscape=None: "telegram message",
    )

    sent_messages = []

    def fake_send(bot_token, chat_id, message):
        sent_messages.append(message)
        return True

    monkeypatch.setattr(main_module, "send_telegram_message", fake_send)

    main_module.main()

    assert sent_messages == ["telegram message"]
    assert store.marked_urls == [article.url]
    assert store.saved is True


def test_failed_telegram_send_does_not_mark_processed_urls(monkeypatch) -> None:
    set_required_env(monkeypatch)
    article = make_article()
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
        "build_telegram_message",
        lambda articles, header="Daily High-Signal Tech Alerts", show_summary=False, daily_trends=None, landscape=None: "telegram message",
    )
    monkeypatch.setattr(main_module, "send_telegram_message", lambda *args: False)

    main_module.main()

    assert store.marked_urls == []
    assert store.saved is False


def test_missing_openai_api_key_uses_rule_based_selector(monkeypatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.delenv("LLM_PROVIDER")
    monkeypatch.delenv("OPENAI_API_KEY")
    articles = [
        make_article(
            "https://example.com/one",
            title="Nvidia GPU demand lifts cloud infrastructure spending",
            source="Reuters",
        ),
        make_article(
            "https://example.com/two",
            title="Celebrity AI meme goes viral",
            source="Unknown Blog",
            snippet="",
        ),
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

    enhancement_called = False

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
        provider=None,
    ):
        nonlocal enhancement_called
        enhancement_called = True
        return articles, DailyLandscape()

    monkeypatch.setattr(main_module, "enhance_message_with_llm", fake_enhance_message_with_llm)

    built_articles = []
    message_headers = []
    show_summary_values = []

    def fake_build_telegram_message(
        curated_articles,
        header="Daily High-Signal Tech Alerts",
        show_summary=False,
        daily_trends=None,
        landscape=None,
    ):
        built_articles.extend(curated_articles)
        message_headers.append(header)
        show_summary_values.append(show_summary)
        assert landscape is not None
        assert landscape.is_empty()
        return "telegram message"

    monkeypatch.setattr(
        main_module,
        "build_telegram_message",
        fake_build_telegram_message,
    )
    monkeypatch.setattr(main_module, "send_telegram_message", lambda *args: True)

    main_module.main()

    assert enhancement_called is False
    assert len(built_articles) == 1
    assert message_headers == ["Daily High-Signal Tech Alerts"]
    assert show_summary_values == [False]
    assert built_articles[0].relevance_score >= 5
    assert "AI Infrastructure" in built_articles[0].why_selected
    assert built_articles[0].korean_summary != articles[0].title
    assert built_articles[0].career_market_insight
    assert store.marked_urls == [article.url for article in built_articles]
    assert store.saved is True


def test_nvidia_provider_uses_nim_configuration(monkeypatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia-model")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("NVIDIA_TIMEOUT_SECONDS", "60")
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

    captured = {}

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
        provider=None,
    ):
        captured["api_key"] = api_key
        captured["model"] = model
        captured["base_url"] = base_url
        captured["timeout_seconds"] = timeout_seconds
        captured["provider"] = provider
        return [curated_article], DailyLandscape(
            headline="AI 인프라 투자 관련 소식이 함께 나타났습니다.",
            themes=[
                TrendTheme(
                    label="AI 인프라 투자",
                    article_indices=[0, 1],
                    summary="GPU와 데이터센터 관련 보도가 함께 나타났습니다.",
                )
            ],
            keywords=["GPU"],
            entities=["NVIDIA"],
        )

    monkeypatch.setattr(main_module, "enhance_message_with_llm", fake_enhance_message_with_llm)
    captured_message = {}

    def fake_build_telegram_message(
        articles,
        header="Daily High-Signal Tech Alerts",
        show_summary=False,
        daily_trends=None,
        landscape=None,
    ):
        captured_message["articles"] = articles
        captured_message["landscape"] = landscape
        captured_message["show_summary"] = show_summary
        return "telegram message"

    monkeypatch.setattr(
        main_module,
        "build_telegram_message",
        fake_build_telegram_message,
    )
    monkeypatch.setattr(main_module, "send_telegram_message", lambda *args: True)

    main_module.main()

    assert captured == {
        "api_key": "nvapi-key",
        "model": "nvidia-model",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "timeout_seconds": 60.0,
        "provider": "nvidia",
    }
    assert captured_message["articles"] == [curated_article]
    assert captured_message["landscape"].headline == "AI 인프라 투자 관련 소식이 함께 나타났습니다."
    assert captured_message["landscape"].themes[0].label == "AI 인프라 투자"
    assert captured_message["landscape"].keywords == ["GPU"]
    assert captured_message["landscape"].entities == ["NVIDIA"]
    assert captured_message["show_summary"] is True
    assert store.marked_urls == [article.url]
    assert store.saved is True


def test_openai_provider_uses_message_enhancement(monkeypatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    article = make_article()
    store = FakeDedupStore()
    store.new_articles = [article]
    monkeypatch.setattr(main_module, "DedupStore", lambda: store)
    monkeypatch.setattr(
        main_module,
        "fetch_recent_google_alerts_html",
        lambda *args: ["<html></html>"],
    )
    monkeypatch.setattr(main_module, "parse_google_alerts_email", lambda html: [article])

    captured = {}

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
        provider=None,
    ):
        captured["api_key"] = api_key
        captured["model"] = model
        captured["base_url"] = base_url
        captured["timeout_seconds"] = timeout_seconds
        captured["provider"] = provider
        return articles, DailyLandscape()

    monkeypatch.setattr(main_module, "enhance_message_with_llm", fake_enhance_message_with_llm)
    monkeypatch.setattr(
        main_module,
        "build_telegram_message",
        lambda articles, header="Daily High-Signal Tech Alerts", show_summary=True, daily_trends=None, landscape=None: "telegram message",
    )
    monkeypatch.setattr(main_module, "send_telegram_message", lambda *args: True)

    main_module.main()

    assert captured == {
        "api_key": "openai-key",
        "model": "gpt-test",
        "base_url": None,
        "timeout_seconds": None,
        "provider": "openai",
    }
