from execution.trade_exit import check_trade_exit
import time

from config import CONFIG
from state import state, load_state, save_state

loaded = load_state()
state.update(loaded)   # 🔥 EZ A HIÁNYZÓ LÉPÉS

print("📦 STATE LOADED:", state)

print("ENGINE STATE ID:", id(state))

from data.candles import get_candle
from strategy.zones import get_zones
from strategy.signals import get_signal
from strategy.fibo import calculate_extension_price

from execution.risk import calculate_position_size
from execution.pnl import calculate_pnl
from execution.paper import open_trade, close_trade

from telegram.bot import send_entry, send_close

import os
print("📁 SAVE PATH:", os.path.abspath("state.json"))


# =========================
# ENGINE LOOP
# =========================

def run_engine():

    print("🚀 MULTI-TF STABLE ENGINE STARTED")


    while True:
        try:

            if not state["running"]:
                time.sleep(CONFIG["paused_delay"])
                continue

            symbol = state["symbol"]

            if state["high"] is None or state["low"] is None:
                print("⏳ Waiting for /set_range...")
                time.sleep(2)
                continue

            # =========================
            # FIBO CONTEXT
            # =========================
            zones = get_zones(state["high"], state["low"])

            if zones is None:
                print("⏳ No zones")
                time.sleep(CONFIG["loop_delay"])
                continue

           
            # =========================
            # ENTRY SCAN (MULTI TF)
            # =========================
            
            for tf in state["timeframes"]:

                candle_data = get_candle(symbol, tf)
                candle = candle_data["current"]
                prev = candle_data["previous"]
                live = candle_data["live"]


                # Mindig ellenőrizzük az exitet
                if state["trade_active"]:
                    check_trade_exit(candle)

                # =========================
                # RANGE INVALID CHECK
                # =========================

                if (
                    state["structure_active"]
                    and not state["range_invalid"]
                    and (
                        live["high"] > state["high"]
                        or live["low"] < state["low"]
                    )
                ):

                    print("🚨 RANGE INVALID!")

                    state["range_invalid"] = True
                    state["structure_active"] = False

                    save_state(state)

                    from telegram.bot import send_message

                    send_message(
                        "🚨 Range Invalid!\n\n"
                        "Current trade (if any) will continue until TP or SL.\n"
                        "No new trades will be opened.\n\n"
                        "Please set a new range:\n"
                        "/range HIGH LOW"
                    )

                ts = candle["timestamp"]

                # TF duplicate lock
                if state["last_candle_ts"].get(tf) == ts:
                    continue

                state["last_candle_ts"][tf] = ts

                # Ha a range érvénytelen, nem keresünk új belépőt
                if state["range_invalid"]:
                    continue

                signal = get_signal(
                    candle=candle,
                    prev_candle=prev,
                    zones=zones,
                    state=state
                )

                if not signal:
                    continue

                # =========================
                # FIRST SIGNAL WINS
                # =========================
                side = signal["side"]
                zone = signal["zone"]
                pattern = signal["pattern"]
                entry = signal["entry_price"]

                print(f"🔥 SIGNAL FROM TF {tf}")

                # =========================
                # SL / TP (0.1%)
                # =========================
                if side == "long":
                    sl = state["low"] * 0.999
                else:
                    sl = state["high"] * 1.001

                tp = calculate_extension_price(
                    side=side,
                    high=state["high"],
                    low=state["low"],
                    level=state["tp_level"]
)

                # =========================
                # POSITION SIZE
                # =========================
                pos_btc, pos_usd = calculate_position_size(
                    state["balance"],
                    state["risk"],
                    entry,
                    sl
                )

                if pos_btc <= 0:
                    continue

                # =========================
                # OPEN TRADE
                # =========================
                open_trade(side, entry, sl, tp, pos_btc, pos_usd, zone)

                state["active_tf"] = tf
                state["entry_candle_close"] = candle["close_time"]

                save_state(state)

                # =========================
                # TELEGRAM ENTRY
                # =========================
                send_entry(
                    side, entry, sl, tp,
                    zone, pattern,
                    pos_btc, pos_usd,
                    tf
                )

                print(f"📊 TRADE OPENED FROM TF {tf}")

                break

            time.sleep(CONFIG["loop_delay"])

        except Exception as e:
            print("❌ ENGINE ERROR:", e)
            time.sleep(CONFIG["error_delay"])