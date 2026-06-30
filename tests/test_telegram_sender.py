import requests

from src import telegram_sender
from src.telegram_sender import send_telegram_message


class Response:
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_empty_message_does_not_call_requests_post(monkeypatch) -> None:
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(telegram_sender.requests, "post", fake_post)

    result = send_telegram_message("token", "chat", "")

    assert result is False
    assert called is False


def test_successful_response_returns_true(monkeypatch) -> None:
    def fake_post(url, data, timeout):
        return Response(200)

    monkeypatch.setattr(telegram_sender.requests, "post", fake_post)

    assert send_telegram_message("token", "chat", "hello") is True


def test_send_telegram_message_uses_html_parse_mode(monkeypatch) -> None:
    sent_payloads = []

    def fake_post(url, data, timeout):
        sent_payloads.append(data)
        return Response(200)

    monkeypatch.setattr(telegram_sender.requests, "post", fake_post)

    assert send_telegram_message("token", "chat", "hello") is True
    assert sent_payloads[0]["parse_mode"] == "HTML"
    assert sent_payloads[0]["disable_web_page_preview"] is True


def test_failed_response_returns_false(monkeypatch) -> None:
    def fake_post(url, data, timeout):
        return Response(500)

    monkeypatch.setattr(telegram_sender.requests, "post", fake_post)

    assert send_telegram_message("token", "chat", "hello") is False


def test_request_exception_returns_false(monkeypatch) -> None:
    def fake_post(url, data, timeout):
        raise requests.RequestException

    monkeypatch.setattr(telegram_sender.requests, "post", fake_post)

    assert send_telegram_message("token", "chat", "hello") is False
