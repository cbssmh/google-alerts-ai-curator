import requests


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    if not message:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
    except requests.RequestException:
        return False

    return 200 <= response.status_code < 300
