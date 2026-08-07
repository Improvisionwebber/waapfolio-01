import requests
from django.conf import settings


def send_telegram_message(message):

    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    if not settings.TELEGRAM_CHAT_ID:
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{settings.TELEGRAM_BOT_TOKEN}"
        "/sendMessage"
    )

    data = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(
            url,
            data=data,
            timeout=10
        )

        return response.json()

    except Exception as e:
        print(e)
        return False