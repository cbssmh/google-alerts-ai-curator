from src.url_normalizer import normalize_url


def test_normalize_url_removes_trailing_slash() -> None:
    assert normalize_url("https://example.com/article/") == "https://example.com/article"


def test_normalize_url_extracts_google_redirect_target() -> None:
    url = "https://www.google.com/url?q=https%3A%2F%2Fexample.com%2Farticle%2F&sa=U"

    assert normalize_url(url) == "https://example.com/article"


def test_normalize_url_removes_tracking_parameters() -> None:
    url = "https://example.com/article?utm_source=google&gclid=123&id=42"

    assert normalize_url(url) == "https://example.com/article?id=42"


def test_normalize_url_tolerates_malformed_url() -> None:
    assert normalize_url("not a url") == "not a url"
