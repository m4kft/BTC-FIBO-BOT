from state import (
    state,
    save_state,
    reset_trade_state,
    factory_reset_state,
    create_symbol_state,
    normalize_symbol_input
)
from strategy.zones import get_zones

import time

print("TG STATE ID:", id(state))

def format_price(price, symbol_state):

    precision = symbol_state.get("price_precision", 2)

    return f"{price:.{precision}f}"
    
# =====================================================
# SET ACTIVE SYMBOL
# =====================================================
def set_active_symbol(symbol):

    clean_symbol, market = normalize_symbol_input(symbol)

    state["active_symbol"] = clean_symbol

    if clean_symbol not in state["symbols"]:
        state["symbols"][clean_symbol] = create_symbol_state()
        state["symbols"][clean_symbol]["market"] = market

    state["symbols"][clean_symbol]["symbol"] = clean_symbol

    save_state(state)

    market_label = state["symbols"][clean_symbol].get("market", "spot")

    return f"📈 Active Symbol: {clean_symbol} ({market_label})"

# =====================================================
# STATUS DASHBOARD
# =====================================================

def build_status():

    msg = "📊 CRYPTO FIBO BOT V5\n\n"

    msg += "════════ ACTIVE SYMBOLS ════════\n\n"

    inactive = []

    for symbol, s in state["symbols"].items():

        active_range = (
            s["structure_active"]
            and not s["range_invalid"]
        )

        active_trade = s["trade_active"]

        # ------------------------------------
        # INACTIVE LIST
        # ------------------------------------

        if not active_range and not active_trade:

            if s["range_invalid"]:
                inactive.append(f"🔴 {symbol}   Range Invalid")
            else:
                inactive.append(f"⚫ {symbol}   No Range")

            continue

        # ------------------------------------
        # HEADER
        # ------------------------------------

        icon = "🟢" if active_trade else "🟡"

        msg += f"{icon} {symbol}\n\n"

        msg += (
            f"Direction   : {s['direction'].upper()}\n"
            f"Range       : ACTIVE ✅\n"
            f"High        : {format_price(s['high'], s)}\n"
            f"Low         : {format_price(s['low'], s)}\n"
            f"TF          : {', '.join(s['timeframes'])}\n\n"
        )

        # ------------------------------------
        # TRADE
        # ------------------------------------

        if active_trade:

            asset = symbol.replace("USDT", "")

            msg += (
                f"Trade       : ACTIVE {s['trade_side'].upper()}\n"
                f"Entry       : {format_price(s['entry'], s)}\n"
                f"SL          : {format_price(s['sl'], s)}\n"
                f"Remaining   : {round(s['remaining_percent'], 2)}%\n"
                f"Trade PnL   : {round(s['trade_pnl'], 2)} USD\n\n"
            )

            msg += (
                f"Position\n"
                f"{asset:<12}: {round(s['pos_btc'], 6)}\n"
                f"USD         : {round(s['pos_usd'], 2)}\n\n"
            )

        else:

            msg += "Trade       : NONE\n\n"

        # ------------------------------------
        # TAKE PROFIT
        # ------------------------------------

        msg += "Take Profit\n\n"

        if len(s["active_targets"]) > 0:

            for i, tp in enumerate(s["active_targets"], start=1):

                icon = "✅" if tp["hit"] else "⏳"

                msg += (
                    f"{icon} TP{i}  {tp['value']}   "
                    f"{tp['percent']}%\n"
                )

        else:

            for i, tp in enumerate(s["tp_config"], start=1):

                msg += (
                    f"⏳ TP{i}  {tp['value']}   "
                    f"{tp['percent']}%\n"
                )

        msg += "\n"

        msg += (
            f"Break Even : {'ON' if s['breakeven_active'] else 'OFF'}\n"
        )

        msg += "\n──────────────────────────────\n\n"

    # ------------------------------------
    # INACTIVE SYMBOLS
    # ------------------------------------

    if inactive:

        msg += "════════ INACTIVE ════════\n\n"

        for item in inactive:

            msg += item + "\n"

        msg += "\n"

    # ------------------------------------
    # ACCOUNT
    # ------------------------------------

    msg += "════════ ACCOUNT ════════\n\n"

    msg += (
        f"Running : {'YES ✅' if state['running'] else 'NO 🔴'}\n\n"
        f"Balance : {round(state['balance'], 2)} USD\n\n"
        f"Wins    : {state['wins']}\n"
        f"Losses  : {state['losses']}\n"
        f"Trades  : {state['total_trades']}\n"
    )

    return msg

def handle_command(text: str):

    text = text.strip()

    # =====================================================
    # HELP
    # =====================================================
    if text == "/help":

        return """
🤖 CRYPTO FIBO BOT V5

══════════ BOT ══════════

/start
/stop
/status
/help

════════ SYMBOL ════════

/add BTCUSDT
/add GWEIUSDT.P   (.P = futures, auto-detect)
/remove BTCUSDT

/symbol BTCUSDT

/market spot
/market futures

Dynamic Symbol Commands

/btc
/eth
/bnb
/bico
/doge
...

════════ DIRECTION ════════

/long
/short

════════ TIMEFRAME ════════

/tf 1m
/tf 5m
/tf 15m
/tf 1h

/tf 1m 5m
/tf 5m 15m
/tf 15m 1h

════════ RANGE ══════════

/range HIGH LOW

Example:
/range 60961 58205

════════ RISK ═══════════

/risk 1

══════ TAKE PROFIT ══════

/tp
/tp clear
/tp reset
/tp add <fibo> <percent>
/tp remove <index>

Examples:

/tp add 1.0 30
/tp add 1.272 30
/tp add 1.618 40

════════ BREAK EVEN ══════

/be on
/be off

════════ INFO ═══════════

/zones

════════ RESET ══════════

/reset_trade
/factory_reset
"""

    # =====================================================
    # START
    # =====================================================
    if text == "/start":
        state["running"] = True
        save_state(state)
        return "✅ Bot Started"

    # =====================================================
    # STOP
    # =====================================================
    if text == "/stop":
        state["running"] = False
        save_state(state)
        return "⛔ Bot Stopped"

    # =====================================================
    # DYNAMIC SYMBOL COMMAND
    # =====================================================
    if text.startswith("/"):

        command = text[1:].upper()

        for symbol in state["symbols"]:

            base = symbol.replace("USDT", "")

            if command == base:

                return set_active_symbol(symbol)

    # =====================================================
    # CUSTOM SYMBOL
    # =====================================================
    if text.startswith("/symbol"):

        try:

            _, symbol = text.split()

            return set_active_symbol(symbol)

        except:
            return "Usage:\n/symbol BTCUSDT"

    # =====================================================
    # ADD SYMBOL
    # =====================================================
    if text.startswith("/add"):

        try:

            _, symbol = text.split()

            clean_symbol, market = normalize_symbol_input(symbol)

            if clean_symbol in state["symbols"]:
                return f"⚠ {clean_symbol} already exists."

            state["symbols"][clean_symbol] = create_symbol_state()
            state["symbols"][clean_symbol]["symbol"] = clean_symbol
            state["symbols"][clean_symbol]["market"] = market

            save_state(state)

            return f"✅ Added: {clean_symbol} ({market})"

        except:
            return "Usage:\n/add BTCUSDT\n/add GWEIUSDT.P  (auto-detects futures)"

    # =====================================================
    # REMOVE SYMBOL
    # =====================================================
    if text.startswith("/remove"):

        try:

            _, symbol = text.split()

            symbol = symbol.upper()

            if symbol not in state["symbols"]:
                return f"❌ {symbol} not found."

            if len(state["symbols"]) == 1:
                return "❌ Cannot remove the last symbol."

            del state["symbols"][symbol]

            if state["active_symbol"] == symbol:
                state["active_symbol"] = next(iter(state["symbols"]))

            save_state(state)

            return f"🗑 Removed: {symbol}"

        except:
            return "Usage:\n/remove BTCUSDT"

    # =====================================================
    # LONG
    # =====================================================
    if text == "/long":

        symbol = state["active_symbol"]

        state["symbols"][symbol]["direction"] = "long"

        save_state(state)

        return f"🟢 {symbol}\nDirection: LONG"

    # =====================================================
    # SHORT
    # =====================================================
    if text == "/short":

        symbol = state["active_symbol"]

        state["symbols"][symbol]["direction"] = "short"

        save_state(state)

        return f"🔴 {symbol}\nDirection: SHORT"

   
    # =====================================================
    # MARKET (SPOT / FUTURES)
    # =====================================================
    if text.startswith("/market"):

        try:
            parts = text.split()
            market = parts[1].lower()

            if market not in ("spot", "futures"):
                return "Usage:\n/market spot\n/market futures"

            symbol = state["active_symbol"]

            state["symbols"][symbol]["market"] = market

            save_state(state)

            return f"🏦 {symbol}\nMarket: {market}"

        except:
            return "Usage:\n/market spot\n/market futures"


    # =====================================================
    # TIMEFRAME
    # =====================================================
    if text.startswith("/tf"):

        try:
            parts = text.split()
            tfs = parts[1:]

            if len(tfs) == 0:
                return "Usage: /tf 5m 15m"

            symbol = state["active_symbol"]

            state["symbols"][symbol]["timeframes"] = tfs

            save_state(state)

            return (
                f"⏱ {symbol}\n"
                f"Timeframes: {state['symbols'][symbol]['timeframes']}"
            )
        except:
            return "Usage: /tf 5m 15m"


    # =====================================================
    # RANGE (FIBO HIGH/LOW)
    # =====================================================
    if text.startswith("/range"):

        try:
            _, high, low = text.split()

            symbol = state["active_symbol"]

            print("\n🔥 RANGE SET")
            print(f"Symbol     : {symbol}")

            state["symbols"][symbol]["high"] = float(high)
            state["symbols"][symbol]["low"] = float(low)

            # Ár pontosság eltárolása
            precision = 0

            if "." in high:
                precision = len(high.split(".")[1])

            state["symbols"][symbol]["price_precision"] = precision

            # Mikor lett beállítva a range?
            state["symbols"][symbol]["range_set_time"] = int(time.time() * 1000)

            state["symbols"][symbol]["structure_active"] = True
            state["symbols"][symbol]["range_invalid"] = False

            # Új range → minden zóna újra használható
            state["symbols"][symbol]["long_zone_used"] = {
                "A": False,
                "B": False,
                "C": False
            }

            state["symbols"][symbol]["short_zone_used"] = {
                "A": False,
                "B": False,
                "C": False
            }

            print(f"High       : {state['symbols'][symbol]['high']}")
            print(f"Low        : {state['symbols'][symbol]['low']}")

            save_state(state)

            print("💾 STATE SAVED")

            return (
                f"📊 Range set for {symbol}\n"
                f"High: {high}\n"
                f"Low: {low}"
            )

        except Exception as e:
            print("❌ RANGE ERROR:", e)
            return "Usage: /range 60961 58205"

    # =====================================================
    # RISK
    # =====================================================
    if text.startswith("/risk"):

        try:
            _, risk = text.split()

            state["risk"] = float(risk)

            save_state(state)

            return f"⚖ Risk set: {state['risk']}%"

        except:
            return "Usage: /risk 1"



    # =====================================================
    # RESET TRADE
    # =====================================================
    if text == "/reset_trade":

        reset_trade_state()

        save_state(state)

        return "✅ Trade reset completed."

    # =====================================================
    # FACTORY RESET
    # =====================================================
    if text == "/factory_reset":

        factory_reset_state()

        save_state(state)

        return "✅ Factory reset completed."

    # =====================================================
    # ZONES DISPLAY
    # =====================================================
    if text == "/zones":

        symbol = state["active_symbol"]
        symbol_state = state["symbols"][symbol]

        if symbol_state["high"] is None or symbol_state["low"] is None:
            return "⚠ No range set"

        zones = get_zones(
            symbol_state["high"],
            symbol_state["low"]
        )
        msg = "📐 FIBO ZONES\n\n"

        msg += "🟩 LONG\n"
        for k, z in zones["long"].items():
            msg += f"{k}: {round(z['low'],2)} → {round(z['high'],2)}\n"

        msg += "\n🟥 SHORT\n"
        for k, z in zones["short"].items():
            msg += f"{k}: {round(z['low'],2)} → {round(z['high'],2)}\n"

        return msg

    # =====================================================
    # TP CONFIG
    # =====================================================
    if text == "/tp":

        symbol = state["active_symbol"]
        symbol_state = state["symbols"][symbol]

        if len(symbol_state["tp_config"]) == 0:
            return "⚠ No TP configured."

        msg = f"📌 TP CONFIGURATION ({symbol})\n\n"

        total = 0

        for i, tp in enumerate(symbol_state["tp_config"], start=1):

            msg += (
                f"{i}. "
                f"Fibo {tp['value']} "
                f"→ {tp['percent']}%\n"
            )

            total += tp["percent"]

        msg += f"\nTotal: {total}%"

        return msg

    # =====================================================
    # TP CLEAR
    # =====================================================
    if text == "/tp clear":

        symbol = state["active_symbol"]
        symbol_state = state["symbols"][symbol]

        symbol_state["tp_config"] = []

        save_state(state)

        return f"🗑 TP configuration cleared for {symbol}."

    # =====================================================
    # TP RESET
    # =====================================================
    if text == "/tp reset":

        symbol = state["active_symbol"]
        symbol_state = state["symbols"][symbol]

        symbol_state["tp_config"] = [
            {
                "type": "fibo",
                "value": 1.0,
                "percent": 100
            }
        ]

        save_state(state)

        return f"♻ TP configuration reset for {symbol}."

    # =====================================================
    # TP ADD
    # =====================================================
    if text.startswith("/tp add"):

        try:

            symbol = state["active_symbol"]
            symbol_state = state["symbols"][symbol]

            _, _, level, percent = text.split()

            level = float(level)
            percent = float(percent)

            if level < 0.5:
                return "❌ Fibonacci level must be >= 0.5"

            if percent <= 0:
                return "❌ Percent must be greater than 0"

            total = sum(tp["percent"] for tp in symbol_state["tp_config"])

            if total + percent > 100:
                return "❌ Total TP percentage cannot exceed 100%"

            symbol_state["tp_config"].append(
                {
                    "type": "fibo",
                    "value": level,
                    "percent": percent
                }
            )

            save_state(state)

            return (
                f"✅ TP added for {symbol}\n\n"
                f"Level: {level}\n"
                f"Percent: {percent}%"
            )

        except:
            return "Usage:\n/tp add 1.618 50"

    # =====================================================
    # TP REMOVE
    # =====================================================
    if text.startswith("/tp remove"):

        try:

            symbol = state["active_symbol"]
            symbol_state = state["symbols"][symbol]

            _, _, index = text.split()

            index = int(index) - 1

            if index < 0 or index >= len(symbol_state["tp_config"]):
                return "❌ Invalid TP index"

            removed = symbol_state["tp_config"].pop(index)

            save_state(state)

            return (
                f"🗑 TP removed from {symbol}\n\n"
                f"Level: {removed['value']}\n"
                f"Percent: {removed['percent']}%"
            )

        except:
            return "Usage:\n/tp remove 2"

    # =====================================================
    # BREAK EVEN ON
    # =====================================================
    if text == "/be on":

        symbol = state["active_symbol"]
        symbol_state = state["symbols"][symbol]

        symbol_state["breakeven_enabled"] = True

        save_state(state)

        return f"🟢 {symbol}\nBreak Even enabled"

    # =====================================================
    # BREAK EVEN OFF
    # =====================================================
    if text == "/be off":

        symbol = state["active_symbol"]
        symbol_state = state["symbols"][symbol]

        symbol_state["breakeven_enabled"] = False

        save_state(state)

        return f"🔴 {symbol}\nBreak Even disabled"

    # =====================================================
    # STATUS
    # =====================================================
    if text == "/status":
        return build_status()

    return "❓ Unknown command (/help)" 
