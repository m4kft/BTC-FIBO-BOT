import time
import requests

from config import CONFIG
from state import state
from telegram.commands import handle_command


TOKEN = CONFIG["telegram_token"]
CHAT_ID = CONFIG["telegram_chat_id"]

LAST_UPDATE_ID = 0


def get_updates():
    global LAST_UPDATE_ID

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    params = {
        "offset": LAST_UPDATE_ID + 1,
        "timeout": 5
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        return res.json()
    except Exception as e:
        print("Telegram poll error:", e)
        return None


def run_telegram_listener():
    global LAST_UPDATE_ID

    print("📲 Telegram control started")

    while True:
        data = get_updates()

        if not data or not data.get("ok"):
            time.sleep(2)
            continue

        for result in data["result"]:
            LAST_UPDATE_ID = result["update_id"]

            message = result.get("message", {})
            text = message.get("text", "")

            if not text:
                continue

            response = handle_command(text)

            try:
                requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    data={
                        "chat_id": CHAT_ID,
                        "text": response
                    }
                )
            except Exception as e:
                print("Telegram send error:", e)

        time.sleep(1)