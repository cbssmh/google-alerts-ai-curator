from email import policy
from email.parser import BytesParser
from pathlib import Path

import pytest

from src.google_alerts_parser import parse_google_alerts_email


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "google_alerts" / "sample_01.eml"
GOOGLE_ALERTS_FIXTURE_DIR = Path(__file__).parent / "google_alerts"


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


def test_parse_google_alerts_email_extracts_snippet_from_fixture() -> None:
    html = load_html_fixture()

    articles = parse_google_alerts_email(html)

    assert any(article.snippet for article in articles)


def test_parse_google_alerts_email_normalizes_and_deduplicates_urls() -> None:
    html = """
    <a href="https://www.google.com/url?q=https%3A%2F%2Fexample.com%2Farticle%2F%3Futm_source%3Dalerts">Article one</a>
    <a href="https://example.com/article">Article duplicate</a>
    """

    articles = parse_google_alerts_email(html)

    assert [article.url for article in articles] == ["https://example.com/article"]


def test_parse_google_alerts_email_skips_google_account_notifications() -> None:
    html = """
    <a href="https://myaccount.google.com/notifications">Security notification</a>
    <a href="https://example.com/article">Real article</a>
    """

    articles = parse_google_alerts_email(html)

    assert [article.url for article in articles] == ["https://example.com/article"]


def test_parse_google_alerts_email_skips_links_whose_text_is_only_a_url() -> None:
    html = '<a href="https://example.com/article">https://example.com/article</a>'

    articles = parse_google_alerts_email(html)

    assert articles == []


def test_parse_google_alerts_email_extracts_source_from_title_text() -> None:
    html = """
    <a href="https://blog.google/article">
      100 things we announced at I/O 2026 - Google Blog
    </a>
    """

    articles = parse_google_alerts_email(html)

    assert articles[0].title == "100 things we announced at I/O 2026"
    assert articles[0].source == "Google Blog"


@pytest.mark.parametrize(
    "source",
    [
        "Reuters",
        "Bloomberg",
        "CNBC",
        "The Economist",
        "Financial Times",
        "The New York Times",
    ],
)
def test_parse_google_alerts_email_extracts_known_pipe_suffix_source(
    source: str,
) -> None:
    html = f"""
    <a href="https://example.com/article">
      Samsung, SK Hynix mega South Korea chips gamble tests optimism of AI cycle | {source}
    </a>
    """

    articles = parse_google_alerts_email(html)

    assert (
        articles[0].title
        == "Samsung, SK Hynix mega South Korea chips gamble tests optimism of AI cycle"
    )
    assert articles[0].source == source


def test_parse_google_alerts_email_leaves_title_without_known_suffix_unchanged() -> None:
    html = """
    <a href="https://example.com/article">
      Nvidia | AMD battle heats up
    </a>
    """

    articles = parse_google_alerts_email(html)

    assert articles[0].title == "Nvidia | AMD battle heats up"
    assert articles[0].source == ""


def test_google_alerts_fixtures_still_parse_articles() -> None:
    fixture_paths = sorted(GOOGLE_ALERTS_FIXTURE_DIR.glob("sample_*.eml"))

    assert fixture_paths

    for fixture_path in fixture_paths:
        with fixture_path.open("rb") as fixture:
            message = BytesParser(policy=policy.default).parse(fixture)

        html = ""
        for part in message.walk():
            if part.get_content_type() == "text/html":
                html = part.get_content()
                break

        articles = parse_google_alerts_email(html)

        assert articles, fixture_path.name


def test_parse_google_alerts_email_extracts_article_description() -> None:
    html = """
    <tr itemtype="http://schema.org/Article">
      <td>
        <a href="https://example.com/article">AI platform shift - Example</a>
        <div itemprop="description">
          Google Alerts snippet with useful market context.
        </div>
      </td>
    </tr>
    """

    articles = parse_google_alerts_email(html)

    assert articles[0].snippet == "Google Alerts snippet with useful market context."


def test_parse_google_alerts_email_missing_description_uses_empty_snippet() -> None:
    html = """
    <tr itemtype="http://schema.org/Article">
      <td>
        <a href="https://example.com/article">AI platform shift - Example</a>
      </td>
    </tr>
    """

    articles = parse_google_alerts_email(html)

    assert articles[0].snippet == ""
