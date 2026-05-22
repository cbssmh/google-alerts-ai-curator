from pathlib import Path

from src.gmail_fetcher import extract_html_bodies_from_message


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "google_alerts" / "sample_01.eml"


def test_extract_html_bodies_from_message_returns_html_from_fixture() -> None:
    raw_message = FIXTURE_PATH.read_bytes()

    html_bodies = extract_html_bodies_from_message(raw_message)

    assert len(html_bodies) > 0
    assert "<html" in html_bodies[0].lower()
