from state import (
    state,
    save_state,
    reset_trade_state,
    factory_reset_state
)
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
🤖 BTC FIBO BOT V4

══════════ BOT ══════════

/start
/stop
/status

════════ SYMBOL ════════

/btc
/eth
/sol
/xrp
/symbol BTCUSDT

═══════ DIRECTION ═══════

/long
/short

═══════ TIMEFRAME ═══════

/tf 1m
/tf 5m
/tf 15m
/tf 1h

/tf 1m 5m
/tf 5m 15m
/tf 15m 1h

════════ RANGE ═════════

/range HIGH LOW

Example:
/range 60961 58205

═════════ RISK ═════════

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

════════ BREAK EVEN ════════

/be on
/be off

═════════ INFO ═════════

/zones

════════ RESET ═════════

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
    # TP CONFIG
    # =====================================================
    if text == "/tp":

        if len(state["tp_config"]) == 0:
            return "⚠ No TP configured."

        msg = "📌 TP CONFIGURATION\n\n"

        total = 0

        for i, tp in enumerate(state["tp_config"], start=1):

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

        state["tp_config"] = []

        save_state(state)

        return "🗑 TP configuration cleared."

    # =====================================================
    # TP RESET
    # =====================================================
    if text == "/tp reset":

        state["tp_config"] = [
            {
                "type": "fibo",
                "value": 1.0,
                "percent": 100
            }
        ]

        save_state(state)

        return "♻ TP configuration reset."

    # =====================================================
    # TP ADD
    # =====================================================
    if text.startswith("/tp add"):

        try:

            _, _, level, percent = text.split()

            level = float(level)
            percent = float(percent)

            if level < 1.0:
                return "❌ Fibonacci level must be >= 1.0"

            if percent <= 0:
                return "❌ Percent must be greater than 0"

            total = sum(tp["percent"] for tp in state["tp_config"])

            if total + percent > 100:
                return "❌ Total TP percentage cannot exceed 100%"

            state["tp_config"].append(
                {
                    "type": "fibo",
                    "value": level,
                    "percent": percent
                }
            )

            save_state(state)

            return (
                f"✅ TP added\n\n"
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

            _, _, index = text.split()

            index = int(index) - 1

            if index < 0 or index >= len(state["tp_config"]):
                return "❌ Invalid TP index"

            removed = state["tp_config"].pop(index)

            save_state(state)

            return (
                f"🗑 TP removed\n\n"
                f"Level: {removed['value']}\n"
                f"Percent: {removed['percent']}%"
            )

        except:
            return "Usage:\n/tp remove 2"

    # =====================================================
    # BREAK EVEN ON
    # =====================================================
    if text == "/be on":

        state["breakeven_enabled"] = True

        save_state(state)

        return "🟢 Break Even enabled"

    # =====================================================
    # BREAK EVEN OFF
    # =====================================================
    if text == "/be off":

        state["breakeven_enabled"] = False

        save_state(state)

        return "🔴 Break Even disabled"

    # =====================================================
    # STATUS
    # =====================================================
    if text == "/status":

        tp_text = ""

        if len(state["tp_config"]) == 0:

            tp_text = "None"

        else:

            for i, tp in enumerate(state["tp_config"], start=1):

                tp_text += (
                    f"{i}. Fibo {tp['value']} → "
                    f"{tp['percent']}%\n"
                )

        return f"""
📊 BTC FIBO BOT STATUS

════════ BOT ════════

Running: {state["running"]}

════════ MARKET ════════

Symbol: {state["symbol"]}
Direction: {state["direction"]}
Timeframes: {state["timeframes"]}

════════ RANGE ════════

High: {state["high"]}
Low : {state["low"]}

════════ RISK ════════

Risk: {state["risk"]}%

════════ TRADE ════════

Active: {state["trade_active"]}
Side: {state["trade_side"]}

════════ TAKE PROFIT ════════

{tp_text}

Break Even: {"ON" if state["breakeven_enabled"] else "OFF"}

════════ ACCOUNT ════════

Balance: {round(state["balance"],2)}

Wins: {state["wins"]}
Losses: {state["losses"]}
Trades: {state["total_trades"]}
"""


    return "❓ Unknown command (/help)" 
