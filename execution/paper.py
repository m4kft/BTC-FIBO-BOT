from state import state, save_state
import time

def open_trade(side, entry, sl, tp, pos_btc, pos_usd, zone):

    # =========================
    # ELSŐ BELÉPŐ
    # =========================
    if not state["trade_active"]:

        state["trade_active"] = True
        state["trade_side"] = side

        state["entry_time"] = int(time.time())

        state["entry"] = entry
        state["sl"] = sl
        state["tp"] = tp

        state["pos_btc"] = pos_btc
        state["pos_usd"] = pos_usd

    # =========================
    # ÚJ BELÉPŐ (SCALE IN)
    # =========================
    elif state["trade_side"] == side:

        old_size = state["pos_btc"]
        new_size = pos_btc

        total_size = old_size + new_size

        avg_entry = (
            state["entry"] * old_size +
            entry * new_size
        ) / total_size

        state["entry"] = avg_entry
        state["pos_btc"] = total_size
        state["pos_usd"] += pos_usd

        # TP és SL marad

    else:
        return

    # =========================
    # ZONE LOCK
    # =========================
    if side == "long":
        state["long_zone_used"][zone] = True
    else:
        state["short_zone_used"][zone] = True

    save_state(state)

    print("\n📌 TRADE OPENED")
    print("Side:", side)
    print("Zone:", zone)
    print("Average Entry:", round(state["entry"], 2))
    print("Total BTC:", round(state["pos_btc"], 6))


def close_trade(result):
    """
    Trade lezárás (csak log).
    """

    print("\n📌 TRADE CLOSED:", result)