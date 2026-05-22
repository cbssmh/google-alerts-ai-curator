from src.dedup_store import DedupStore
from src.models import Article


def test_new_url_is_not_processed(tmp_path) -> None:
    store = DedupStore(tmp_path / "processed_urls.json")

    assert not store.is_processed("https://example.com/article")


def test_marked_url_becomes_processed(tmp_path) -> None:
    store = DedupStore(tmp_path / "processed_urls.json")

    store.mark_processed("https://example.com/article")

    assert store.is_processed("https://example.com/article")


def test_state_persists_after_save_and_reload(tmp_path) -> None:
    path = tmp_path / "processed_urls.json"
    store = DedupStore(path)
    store.mark_processed("https://example.com/article")
    store.save()

    reloaded_store = DedupStore(path)

    assert reloaded_store.is_processed("https://example.com/article")


def test_malformed_json_does_not_crash(tmp_path) -> None:
    path = tmp_path / "processed_urls.json"
    path.write_text("{not valid json", encoding="utf-8")

    store = DedupStore(path)

    assert not store.is_processed("https://example.com/article")


def test_filter_new_articles_removes_processed_article_urls(tmp_path) -> None:
    store = DedupStore(tmp_path / "processed_urls.json")
    store.mark_processed("https://example.com/article?utm_source=google")
    articles = [
        Article(title="Old", source="", url="https://example.com/article", snippet=""),
        Article(title="New", source="", url="https://example.com/new", snippet=""),
    ]

    new_articles = store.filter_new_articles(articles)

    assert new_articles == [articles[1]]
