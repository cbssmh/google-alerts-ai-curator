import email
import imaplib
from datetime import datetime, timedelta
from email import policy


def fetch_recent_google_alerts_html(
    gmail_email: str,
    app_password: str,
    hours: int = 24,
) -> list[str]:
    since = (datetime.now() - timedelta(hours=hours)).strftime("%d-%b-%Y")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    try:
        mail.login(gmail_email, app_password)
        mail.select("INBOX", readonly=True)

        message_ids = _search_message_ids(
            mail,
            f'(SINCE "{since}" FROM "googlealerts-noreply@google.com")',
        )
        if not message_ids:
            message_ids = _search_message_ids(mail, f'(SINCE "{since}")')

        html_bodies: list[str] = []
        for message_id in message_ids:
            status, data = mail.fetch(message_id, "(BODY.PEEK[])")
            if status != "OK":
                continue

            for item in data:
                if isinstance(item, tuple):
                    html_bodies.extend(extract_html_bodies_from_message(item[1]))

        return html_bodies
    finally:
        try:
            mail.logout()
        except imaplib.IMAP4.error:
            pass


def extract_html_bodies_from_message(raw_message: bytes) -> list[str]:
    message = email.message_from_bytes(raw_message, policy=policy.default)
    html_bodies: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/html":
                html_bodies.append(part.get_content())
    elif message.get_content_type() == "text/html":
        html_bodies.append(message.get_content())

    return html_bodies


def _search_message_ids(mail: imaplib.IMAP4_SSL, criteria: str) -> list[bytes]:
    status, data = mail.search(None, criteria)
    if status != "OK" or not data:
        return []

    return data[0].split()
