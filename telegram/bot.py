from config import CONFIG
from state import state
import requests
from utils.debug import debug

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

def send_entry(symbol_state, side, entry, sl, tp, zone, pattern, pos_btc, pos_usd, tf):

    debug(
        "ENTRY",
        f"""
    Symbol : {symbol_state["symbol"]}
    TF     : {tf}
    Side   : {side}
    Zone   : {zone}
    Pattern: {pattern}

    Entry  : {format_price(entry, symbol_state)}
    SL     : {format_price(sl, symbol_state)}
    """
    )

    symbol = symbol_state["symbol"]
    asset = symbol.replace("USDT", "")

    tp_text = ""

    if len(symbol_state["active_targets"]) == 0:

        tp_text = f"🎯 TP: {format_price(tp, symbol_state)}"

    else:

        for i, target in enumerate(symbol_state["active_targets"], start=1):

            tp_text += (
                f"TP{i} | Fibo {target['value']}\n"
                f"Price: {format_price(target['price'], symbol_state)}\n"
                f"Close: {target['percent']}%\n\n"
            )

    msg = f"""
🚀 ENTRY SIGNAL

📈 Symbol: {symbol}

📊 TF: {tf}
📍 Side: {side.upper()}
📦 Zone: {zone}
🧠 Pattern: {pattern}

💰 Entry: {format_price(entry, symbol_state)}
⛔ SL: {format_price(sl, symbol_state)}

🎯 TAKE PROFIT

{tp_text}

📦 Position

{asset}: {round(pos_btc, 6)}
USD   : {round(pos_usd, 2)}

💰 Balance: {round(state["balance"], 2)} USD
"""

    send_message(msg)

# =========================
# CLOSE MESSAGE
# =========================

def send_close(symbol_state, result, pnl, tf=None):

    symbol = symbol_state["symbol"]

    msg = f"""
📉 TRADE CLOSED

📈 Symbol: {symbol}

📊 TF: {tf}
📋 Result: {result}

💵 Trade PnL: {round(pnl, 2)} USD

💰 Balance: {round(state["balance"], 2)} USD
"""
    send_message(msg)

# =========================
# TP HIT MESSAGE
# =========================

def send_tp_hit(symbol_state, tp_number, target, remaining_percent, trade_pnl, breakeven_active):

    symbol = symbol_state["symbol"]

    msg = f"""
🎯 TAKE PROFIT HIT

📈 Symbol: {symbol}

🏁 TP{tp_number}

📐 Fibo:
{target["value"]}

💰 Price:
{format_price(target["price"], symbol_state)}

📤 Closed:
{target["percent"]}%

📦 Remaining:
{remaining_percent}%

💵 Trade PnL:
{round(trade_pnl, 2)} USD

🛡 Break Even:
{"ON" if breakeven_active else "OFF"}
"""

    send_message(msg)

# =========================
# PRICE FORMAT
# =========================
def format_price(price, symbol_state):

    precision = symbol_state.get("price_precision", 2)

    return f"{price:.{precision}f}"