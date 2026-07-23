from config import CONFIG
from state import state
import requests


TOKEN = CONFIG["telegram_token"]
CHAT_ID = CONFIG["telegram_chat_id"]

def send_message(text: str):
    if not CONFIG.get("telegram_enabled", True):
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# ENTRY MESSAGE
# =========================

def send_entry(side, entry, sl, tp, zone, pattern, pos_btc, pos_usd, tf):
    msg = f"""
🚀 ENTRY SIGNAL

📊 TF: {tf}
📍 Side: {side.upper()}
📦 Zone: {zone}
🧠 Pattern: {pattern}

💰 Entry: {entry}
⛔ SL: {sl}
🎯 TP: {tp}

📦 Position:
BTC: {round(pos_btc, 6)}
USD: {round(pos_usd, 2)}

💰 Balance: {state["balance"]}
"""
    send_message(msg)


# =========================
# CLOSE MESSAGE
# =========================

def send_close(result, pnl, tf=None):
    msg = f"""
📉 TRADE CLOSED

📊 TF: {tf}
Result: {result}
PnL: {round(pnl, 2)} USD

💰 Balance: {state["balance"]}
"""
    send_message(msg)