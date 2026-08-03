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

    tp_text = ""

    if len(state["active_targets"]) == 0:

        tp_text = f"🎯 TP: {round(tp, 2)}"

    else:

        for i, target in enumerate(state["active_targets"], start=1):

            tp_text += (
                f"TP{i} | Fibo {target['value']}\n"
                f"Price: {round(target['price'],2)}\n"
                f"Close: {target['percent']}%\n\n"
            )

    msg = f"""
🚀 ENTRY SIGNAL

📊 TF: {tf}
📍 Side: {side.upper()}
📦 Zone: {zone}
🧠 Pattern: {pattern}

💰 Entry: {round(entry,2)}
⛔ SL: {round(sl,2)}

🎯 TAKE PROFIT

{tp_text}

📦 Position

BTC: {round(pos_btc, 6)}
USD: {round(pos_usd, 2)}

💰 Balance: {round(state["balance"],2)}
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

# =========================
# TP HIT MESSAGE
# =========================

def send_tp_hit(tp_number, target, remaining_percent, trade_pnl, breakeven_active):

    msg = f"""
🎯 TAKE PROFIT HIT

🏁 TP{tp_number}

📐 Fibo:
{target["value"]}

💰 Price:
{round(target["price"], 2)}

📤 Closed:
{target["percent"]}%

📦 Remaining:
{remaining_percent}%

💵 Trade PnL:
{round(trade_pnl, 2)} USD

🛡 Break Even:
{"ACTIVE 🟢" if breakeven_active else "OFF 🔴"}
"""

    send_message(msg)