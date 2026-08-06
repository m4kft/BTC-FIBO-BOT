from state import state, save_state
import time
from strategy.fibo import calculate_extension_price


def open_trade(symbol_state, side, entry, sl, tp, pos_btc, pos_usd, zone):

    # =========================
    # ELSŐ BELÉPŐ
    # =========================
    if not symbol_state["trade_active"]:

        symbol_state["trade_active"] = True
        symbol_state["trade_side"] = side

        symbol_state["entry_time"] = int(time.time())

        symbol_state["entry"] = entry
        symbol_state["sl"] = sl
        symbol_state["tp"] = tp

        symbol_state["pos_btc"] = pos_btc
        symbol_state["pos_usd"] = pos_usd

        symbol_state["initial_pos_btc"] = pos_btc
        symbol_state["initial_pos_usd"] = pos_usd

        symbol_state["trade_pnl"] = 0.0

    # =========================
    # ÚJ BELÉPŐ (SCALE IN)
    # =========================
    elif symbol_state["trade_side"] == side:

        old_size = symbol_state["pos_btc"]
        new_size = pos_btc

        total_size = old_size + new_size

        avg_entry = (
            symbol_state["entry"] * old_size +
            entry * new_size
        ) / total_size

        symbol_state["entry"] = avg_entry
        symbol_state["pos_btc"] = total_size
        symbol_state["pos_usd"] += pos_usd
        symbol_state["initial_pos_btc"] = total_size
        symbol_state["initial_pos_usd"] += pos_usd

        # TP és SL marad

    else:
        return

    # =========================
    # TP TARGETS
    # =========================

    symbol_state["active_targets"] = []

    for tp in symbol_state["tp_config"]:

        if tp["type"] == "fibo":

            price = calculate_extension_price(
                side,
                symbol_state["high"],
                symbol_state["low"],
                tp["value"]
            )

        else:
            continue

        symbol_state["active_targets"].append(
            {
                "type": tp["type"],
                "value": tp["value"],
                "price": price,
                "percent": tp["percent"],
                "hit": False
            }
        )

    symbol_state["remaining_percent"] = 100.0
    symbol_state["breakeven_active"] = False

    # =========================
    # ZONE LOCK
    # =========================
    if side == "long":
        symbol_state["long_zone_used"][zone] = True
    else:
        symbol_state["short_zone_used"][zone] = True

    save_state(state)

    asset = symbol_state["symbol"].replace("USDT", "")

    print("\n📌 TRADE OPENED")
    print(f"Symbol       : {symbol_state['symbol']}")
    print(f"Side         : {side.upper()}")
    print(f"Zone         : {zone}")
    print(f"Average Entry: {round(symbol_state['entry'], 2)}")
    print()
    print("Position")
    print(f"{asset:<13}: {round(symbol_state['pos_btc'], 6)}")
    print(f"USD          : {round(symbol_state['pos_usd'], 2)}")


def close_trade(symbol_state, result):
    """
    Trade lezárás (csak log).
    """

    print("\n📌 TRADE CLOSED")
    print(f"Symbol : {symbol_state['symbol']}")
    print(f"Result : {result}")