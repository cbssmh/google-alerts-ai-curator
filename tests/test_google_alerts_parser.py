from email import policy
from email.parser import BytesParser
from pathlib import Path

from src.google_alerts_parser import parse_google_alerts_email


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "google_alerts" / "sample_01.eml"


def load_html_fixture() -> str:
    with FIXTURE_PATH.open("rb") as fixture:
        message = BytesParser(policy=policy.default).parse(fixture)

    for part in message.walk():
        if part.get_content_type() == "text/html":
            return part.get_content()

    raise AssertionError("Fixture does not contain an HTML body")


def test_parse_google_alerts_email_returns_articles() -> None:
    html = load_html_fixture()

    articles = parse_google_alerts_email(html)

    assert isinstance(articles, list)
    assert len(articles) > 0
    assert articles[0].title
    assert articles[0].url


def test_parse_google_alerts_email_normalizes_and_deduplicates_urls() -> None:
    html = """
    <a href="https://www.google.com/url?q=https%3A%2F%2Fexample.com%2Farticle%2F%3Futm_source%3Dalerts">Article one</a>
    <a href="https://example.com/article">Article duplicate</a>
    """

    articles = parse_google_alerts_email(html)

    assert [article.url for article in articles] == ["https://example.com/article"]
