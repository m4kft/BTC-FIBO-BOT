from execution.trade_exit import check_trade_exit
import time
import traceback

from config import CONFIG
from state import state, save_state

# MEGJEGYZÉS: a state betöltése (initialize_state()) most már
# explicit módon, a main.py-ban történik, MIELŐTT ez a modul
# bármit használna a state-ből. Ne tegyünk ide rejtett
# import-mellékhatást - lásd a korábbi hibajavítás jegyzetét.

from data.candles import get_candle
from data.binance_ws import get_candle_ws
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

                    # =========================
                    # CANDLE LEKÉRÉS - WS ELSŐDLEGES, REST FALLBACK
                    # =========================
                    # Elsőként a websocket cache-ből próbáljuk (gyors,
                    # nem blokkol, nem hívja a hálózatot minden körben).
                    # Ha még nincs rá adat (pl. most lett hozzáadva a
                    # symbol) vagy elavult (STALE_SECONDS-nél régebbi),
                    # visszaesünk a bevált REST hívásra - így ha a
                    # websocket bármiért nem működne, a bot nem áll le,
                    # csak a régi (lassabb, de működő) módon folytatja.
                    #
                    # Ha EZ a symbol/timeframe hibázik REST fallback
                    # közben is, ne akadjon meg emiatt a TÖBBI symbol
                    # vizsgálata is ugyanebben a körben - csak ezt a
                    # timeframe-et hagyjuk ki, és megyünk tovább a
                    # következőre.
                    try:
                        market = symbol_state.get("market", "spot")

                        candle_data = get_candle_ws(symbol, tf, market)

                        if candle_data is None:
                            candle_data = get_candle(symbol, tf)

                    except Exception as e:
                        print(f"⚠ CANDLE FETCH ERROR ({symbol} {tf}): {e}")
                        continue

                    candle = candle_data["current"]
                    prev = candle_data["previous"]
                    live = candle_data["live"]

                        
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

                    # =========================
                    # TRADE EXIT
                    # =========================
                    # FONTOS: ennek FÜGGETLENNEK kell lennie a
                    # range_invalid állapottól és a TF duplicate
                    # lock-tól is - a "live" ár minden körben
                    # változhat, a nyitott pozíció TP/SL/BE
                    # ellenőrzése nem várhat egy új gyertyazárásra,
                    # és pláne nem állhat le csak azért, mert a
                    # range időközben érvénytelenné vált.
                    #
                    # (Korábban ez a blokk a range_invalid check
                    # UTÁN futott - emiatt egy invalidálódott range
                    # esetén a nyitott pozíció TP/SL ellenőrzése
                    # teljesen leállt, és csak egy bot-újraindítás
                    # (recovery.py) tudta pótolni utólag. Ez sértette
                    # a "Range Invalid nem zár trade-et" szabályt.)

                    if symbol_state["trade_active"]:
                        check_trade_exit(symbol_state, live)

                    # TF duplicate lock
                    # (ez mostantól csak az ÚJ BELÉPÉS keresésre
                    # vonatkozik, az exit check-re nem)
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
