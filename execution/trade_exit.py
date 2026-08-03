from state import state, save_state
from execution.pnl import calculate_pnl
from execution.paper import close_trade
from telegram.bot import send_close, send_tp_hit


def check_trade_exit(candle):

    if not state["trade_active"]:
        return False

    side = state["trade_side"]
    entry = state["entry"]
    sl = state["sl"]
    active_targets = state.get("active_targets", [])
    pos_btc = state["pos_btc"]

    high = candle["high"]
    low = candle["low"]

    result = None
    exit_price = None
    tp_hit = None

    # =========================
    # TP TARGET CHECK
    # =========================

    for target in active_targets:

        if target["hit"]:
            continue

        if side == "long":

            if high >= target["price"]:
                tp_hit = target
                exit_price = target["price"]
                break

        else:

            if low <= target["price"]:
                tp_hit = target
                exit_price = target["price"]
                break

    # =========================
    # SL CHECK
    # =========================

    if side == "long":

        if low <= sl:

            if state["breakeven_active"] and sl == entry:
                result = "BE"
            else:
                result = "LOSS"

            exit_price = sl

    else:

        if high >= sl:

            if state["breakeven_active"] and sl == entry:
                result = "BE"
            else:
                result = "LOSS"

            exit_price = sl


    # =========================
    # TP FOUND
    # =========================

    if tp_hit is not None:


        result = "WIN"

    if result is None:
        return False

    # =========================
    # PARTIAL TP
    # =========================

    if tp_hit is not None:

        close_percent = tp_hit["percent"] / 100.0

        close_btc = (
            state["initial_pos_btc"]
            * close_percent
        )

        close_usd = (
            state["initial_pos_usd"]
            * close_percent
        )

        pnl = calculate_pnl(
            entry,
            exit_price,
            close_btc,
            side
        )

        state["balance"] += pnl
        state["trade_pnl"] += pnl

        state["pos_btc"] -= close_btc
        state["pos_usd"] -= close_usd

        # Lebegőpontos védelem
        if state["pos_btc"] < 0:
            state["pos_btc"] = 0

        if state["pos_usd"] < 0:
            state["pos_usd"] = 0

        state["remaining_percent"] -= tp_hit["percent"]

        tp_hit["hit"] = True

        tp_number = (
            state["active_targets"].index(tp_hit) + 1
        )

        # Ne menjen negatívba lebegőpontos hiba miatt
        if state["remaining_percent"] < 0:
            state["remaining_percent"] = 0

        print(
            f"🎯 TP HIT {tp_hit['value']} | "
            f"{tp_hit['percent']}% CLOSED"
        )


        # =========================
        # BREAK EVEN
        # =========================

        if (
            state["breakeven_enabled"]
            and not state["breakeven_active"]
            and state["remaining_percent"] > 0
        ):

            state["sl"] = state["entry"]
            state["breakeven_active"] = True

            print("🟢 BREAK EVEN ACTIVATED")

        send_tp_hit(

            tp_number,

            tp_hit,

            state["remaining_percent"],

            state["trade_pnl"],

            state["breakeven_active"]

        )

        # Ha ez volt az utolsó TP,
        # a maradék pozíció már 0.
        if state["remaining_percent"] <= 0:
            pass

        # Ha ez nem az utolsó TP, akkor marad nyitva a trade
        if state["remaining_percent"] > 0:

            # Trade továbbra is aktív.
            # Nem kereshet új belépőt.
            state["trade_active"] = True

            save_state(state)

        else:

            # Az utolsó TP után is mentsük el az állapotot,
            # mielőtt a végleges lezárás lefut.
            save_state(state)

        if state["remaining_percent"] > 0:

            print(
                f"📦 Remaining position: {state['remaining_percent']}%"
            )

            print("⏳ Trade remains active.")

            return False
            
    # =========================
    # FINAL CLOSE
    # =========================

    pnl = 0

    if result in ("LOSS", "BE"):

        pnl = calculate_pnl(
            entry,
            exit_price,
            state["pos_btc"],
            side
        )

        state["balance"] += pnl
        state["trade_pnl"] += pnl

    elif result == "WIN" and state["remaining_percent"] <= 0:

         # Az utolsó TP PnL-je már a PARTIAL TP
         # blokkban elszámolásra került.
         pnl = 0

    # =========================
    # STATS
    # =========================

    if result == "WIN" and tp_hit is not None:

        state["wins"] += (
            tp_hit["percent"] / 100.0
        )

    elif result == "LOSS":

        loss_part = state["remaining_percent"] / 100.0

        state["losses"] += loss_part

    elif result == "BE":

        pass

    # =========================
    # FINAL TRADE CLOSE
    # =========================

    if state["remaining_percent"] <= 0 or result in ("LOSS", "BE"):

        state["total_trades"] += 1

        send_close(
            result,
            state["trade_pnl"],
            state.get("active_tf")
        )

        print(f"📉 TRADE CLOSED | {result}")

        close_trade(result)

        state["trade_active"] = False
        state["trade_side"] = None
        state["entry"] = 0
        state["sl"] = 0
        state["tp"] = 0
        state["pos_btc"] = 0
        state["pos_usd"] = 0
        state["initial_pos_btc"] = 0
        state["initial_pos_usd"] = 0
        state["remaining_percent"] = 0
        state["trade_pnl"] = 0.0
        state["breakeven_active"] = False
        state["entry_time"] = None
        state["entry_candle_close"] = None

        save_state(state)

        return True