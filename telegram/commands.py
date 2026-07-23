from state import state, save_state
from strategy.zones import get_zones

import time

print("TG STATE ID:", id(state))

def handle_command(text: str):

    text = text.strip()

    # =====================================================
    # HELP
    # =====================================================
    if text == "/help":

        return """
🤖 FIBO BOT COMMANDS

▶ BOT
/start
/stop
/status

▶ SYMBOL
/btc
/eth
/sol
/xrp
/symbol BTCUSDT

▶ DIRECTION
/long
/short
/both

▶ TIMEFRAME
/tf 1m
/tf 1m 5m
/tf 1m 5m 15m
/tf 5m 15m 1h

▶ RANGE
/range HIGH LOW

Example:
/range 60961 58205

▶ RISK
/risk 1

▶ INFO
/zones

▶ RESET
/reset
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
    # BTC
    # =====================================================
    if text == "/btc":
        state["symbol"] = "BTCUSDT"
        save_state(state)
        return "📈 Symbol: BTCUSDT"

    # =====================================================
    # ETH
    # =====================================================
    if text == "/eth":
        state["symbol"] = "ETHUSDT"
        save_state(state)
        return "📈 Symbol: ETHUSDT"

    # =====================================================
    # SOL
    # =====================================================
    if text == "/sol":
        state["symbol"] = "SOLUSDT"
        save_state(state)
        return "📈 Symbol: SOLUSDT"

    # =====================================================
    # XRP
    # =====================================================
    if text == "/xrp":
        state["symbol"] = "XRPUSDT"
        save_state(state)
        return "📈 Symbol: XRPUSDT"

    # =====================================================
    # CUSTOM SYMBOL
    # =====================================================
    if text.startswith("/symbol"):

        try:

            _, symbol = text.split()

            state["symbol"] = symbol.upper()

            save_state(state)

            return f"📈 Symbol: {state['symbol']}"

        except:
            return "Usage:\n/symbol BTCUSDT"

    # =====================================================
    # LONG
    # =====================================================
    if text == "/long":

        state["direction"] = "long"

        save_state(state)

        return "🟢 Direction: LONG"

    # =====================================================
    # SHORT
    # =====================================================
    if text == "/short":

        state["direction"] = "short"

        save_state(state)

        return "🔴 Direction: SHORT"

    # =====================================================
    # BOTH
    # =====================================================
    if text == "/both":

        state["direction"] = "both"

        save_state(state)

        return "🟡 Direction: BOTH"

           # =====================================================
    # TIMEFRAME
    # =====================================================
    if text.startswith("/tf"):

        try:
            parts = text.split()
            tfs = parts[1:]

            if len(tfs) == 0:
                return "Usage: /tf 5m 15m"

            state["timeframes"] = tfs

            save_state(state)

            return f"⏱ Timeframes set: {state['timeframes']}"

        except:
            return "Usage: /tf 5m 15m"


    # =====================================================
    # RANGE (FIBO HIGH/LOW)
    # =====================================================
    if text.startswith("/range"):

        print("🔥 RANGE COMMAND:", text)

        try:
            _, high, low = text.split()

            state["high"] = float(high)
            state["low"] = float(low)

            # Mikor lett beállítva a range?
            state["range_set_time"] = int(time.time() * 1000)

            state["structure_active"] = True
            state["range_invalid"] = False

            # Új range → minden zóna újra használható
            state["long_zone_used"] = {
                "A": False,
                "B": False,
                "C": False
            }

            state["short_zone_used"] = {
                "A": False,
                "B": False,
                "C": False
            }

            print("STATE HIGH:", state["high"])
            print("STATE LOW :", state["low"])

            save_state(state)

            import inspect

            print(save_state)
            print(inspect.getsourcefile(save_state))

            print("💾 STATE SAVED")

            return f"📊 Range set\nHigh: {high}\nLow: {low}"

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
    # RESET ZONES
    # =====================================================
    if text == "/reset":

        state["long_zone_used"] = {"A": False, "B": False, "C": False}
        state["short_zone_used"] = {"A": False, "B": False, "C": False}

        save_state(state)

        return "♻ Zones reset"


    # =====================================================
    # ZONES DISPLAY
    # =====================================================
    if text == "/zones":

        if state["high"] is None or state["low"] is None:
            return "⚠ No range set"

        zones = get_zones(state["high"], state["low"])

        msg = "📐 FIBO ZONES\n\n"

        msg += "🟩 LONG\n"
        for k, z in zones["long"].items():
            msg += f"{k}: {round(z['low'],2)} → {round(z['high'],2)}\n"

        msg += "\n🟥 SHORT\n"
        for k, z in zones["short"].items():
            msg += f"{k}: {round(z['low'],2)} → {round(z['high'],2)}\n"

        return msg


    # =====================================================
    # STATUS
    # =====================================================
    if text == "/status":

        return f"""
📊 STATUS

Running: {state["running"]}
Symbol: {state["symbol"]}
Direction: {state["direction"]}
Timeframes: {state["timeframes"]}

Range:
High: {state["high"]}
Low : {state["low"]}

Risk: {state["risk"]}

Trade Active: {state["trade_active"]}
Side: {state["trade_side"]}

Balance: {state["balance"]}
Wins: {state["wins"]}
Losses: {state["losses"]}
Total: {state["total_trades"]}
"""


    return "❓ Unknown command (/help)" 
