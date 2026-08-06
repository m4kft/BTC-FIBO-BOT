from execution.trade_exit import check_trade_exit
import time
import traceback

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

            # =========================
            # SCAN EVERY SYMBOL
            # =========================

            for symbol, symbol_state in list(state["symbols"].items()):

                if symbol_state["high"] is None or symbol_state["low"] is None:
                    continue

                # =========================
                # FIBO CONTEXT
                # =========================
                zones = get_zones(
                    symbol_state["high"],
                    symbol_state["low"]
                )

                if zones is None:
                    continue

                # =========================
                # ENTRY SCAN (MULTI TF)
                # =========================

                for tf in symbol_state["timeframes"]:

                    candle_data = get_candle(symbol, tf)
                    candle = candle_data["current"]
                    prev = candle_data["previous"]
                    live = candle_data["live"]

                    # Mindig ellenőrizzük az exitet
                    if symbol_state["trade_active"]:
                        check_trade_exit(symbol_state, live)

                    # Ha a trade még mindig aktív,
                    # nem keresünk új belépőt.
                    if symbol_state["trade_active"]:
                        continue
                        
                    # =========================
                    # RANGE INVALID CHECK
                    # =========================

                    if (
                        symbol_state["structure_active"]
                        and not symbol_state["range_invalid"]
                        and (
                            live["high"] >= symbol_state["high"]
                            or
                            live["low"] <= symbol_state["low"]
                        )
                    ):

                        print("🚨 RANGE INVALID!")

                        symbol_state["range_invalid"] = True
                        symbol_state["structure_active"] = False

                        save_state(state)

                        from telegram.bot import send_message

                        send_message(
                            f"🚨 RANGE INVALID\n\n"
                            f"📈 Symbol: {symbol}\n\n"
                            f"Current trade (if any) will continue until TP or SL.\n"
                            f"No new trades will be opened for this symbol.\n\n"
                            f"Please set a new range:\n"
                            f"/range HIGH LOW"
                        )

                    ts = candle["timestamp"]

                    # TF duplicate lock
                    if symbol_state["last_candle_ts"].get(tf) == ts:
                        continue

                    symbol_state["last_candle_ts"][tf] = ts

                    # Ha a range érvénytelen, nem keresünk új belépőt
                    if symbol_state["range_invalid"]:
                        continue

                    signal = get_signal(
                        candle=candle,
                        prev_candle=prev,
                        zones=zones,
                        state=symbol_state
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
                        sl = symbol_state["low"] * 0.999
                    else:
                        sl = symbol_state["high"] * 1.001

                    tp = calculate_extension_price(
                        side=side,
                        high=symbol_state["high"],
                        low=symbol_state["low"],
                        level=symbol_state["tp_level"]
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
                    open_trade(
                        symbol_state,
                        side,
                        entry,
                        sl,
                        tp,
                        pos_btc,
                        pos_usd,
                        zone
                    )

                    symbol_state["active_tf"] = tf
                    symbol_state["entry_candle_close"] = candle["close_time"]

                    save_state(state)

                    # =========================
                    # TELEGRAM ENTRY
                    # =========================

                    send_entry(
                        symbol_state,
                        side,
                        entry,
                        sl,
                        tp,
                        zone,
                        pattern,
                        pos_btc,
                        pos_usd,
                        tf
                    )

                    print(f"📊 TRADE OPENED FROM TF {tf}")

                    break

            time.sleep(CONFIG["loop_delay"])

        except Exception as e:
                print("❌ ENGINE ERROR:", e)
                traceback.print_exc()
                time.sleep(CONFIG["error_delay"])
