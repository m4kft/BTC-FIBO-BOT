from state import state, save_state
from execution.pnl import calculate_pnl
from execution.paper import close_trade
from telegram.bot import send_close, send_tp_hit


def check_trade_exit(symbol_state, candle):

    if not symbol_state["trade_active"]:
        return False

    side = symbol_state["trade_side"]
    entry = symbol_state["entry"]
    sl = symbol_state["sl"]
    active_targets = symbol_state.get("active_targets", [])
    pos_btc = symbol_state["pos_btc"]

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

            if symbol_state["breakeven_active"] and sl == entry:
                result = "BE"
            else:
                result = "LOSS"

            exit_price = sl

    else:

        if high >= sl:

            if symbol_state["breakeven_active"] and sl == entry:
                result = "BE"
            else:
                result = "LOSS"

            exit_price = sl

    # =========================
    # TP FOUND
    # =========================
    #
    # FONTOS: ha ugyanazon a gyertyán/ellenőrzésen belül
    # MIND a SL, MIND a TP szint teljesülne, OHLC adatból nem
    # állapítható meg biztosan, hogy melyik történt előbb.
    # Ezért itt konzervatívan a SL-t részesítjük előnyben
    # (worst-case feltételezés), hogy a bot sose mutasson
    # optimistább eredményt a valóságosnál.
    #
    # A régi kód itt feltétel nélkül felülírta a "LOSS"
    # eredményt "WIN"-re, ha a TP is teljesült - ez hamisan
    # javította a statisztikát minden olyan esetben, amikor
    # egy gyertya mindkét szintet érintette.

    if result is None and tp_hit is not None:

        result = "WIN"

    if result is None:
        return False
    # =========================
    # PARTIAL TP
    # =========================
    # Csak akkor foglalunk el részleges profitot, ha a TP
    # valóban "megnyerte" a versenyt a SL-lel szemben
    # (result == "WIN"). Ha a SL élvezett elsőbbséget, ne
    # könyveljünk el semmilyen TP-részletet.

    if tp_hit is not None and result == "WIN":

        close_percent = tp_hit["percent"] / 100.0

        close_btc = (
            symbol_state["initial_pos_btc"]
            * close_percent
        )

        close_usd = (
            symbol_state["initial_pos_usd"]
            * close_percent
        )

        pnl = calculate_pnl(
            entry,
            exit_price,
            close_btc,
            side
        )

        state["balance"] += pnl
        symbol_state["trade_pnl"] += pnl

        symbol_state["pos_btc"] -= close_btc
        symbol_state["pos_usd"] -= close_usd

        # Lebegőpontos védelem
        if symbol_state["pos_btc"] < 0:
            symbol_state["pos_btc"] = 0

        if symbol_state["pos_usd"] < 0:
            symbol_state["pos_usd"] = 0

        symbol_state["remaining_percent"] -= tp_hit["percent"]

        tp_hit["hit"] = True

        tp_number = (
            symbol_state["active_targets"].index(tp_hit) + 1
        )

        # Ne menjen negatívba lebegőpontos hiba miatt
        if symbol_state["remaining_percent"] < 0:
            symbol_state["remaining_percent"] = 0

        asset = symbol_state["symbol"].replace("USDT", "")

        print("\n🎯 TAKE PROFIT HIT")
        print(f"Symbol       : {symbol_state['symbol']}")
        print(f"TP           : TP{tp_number}")
        print(f"Fibo         : {tp_hit['value']}")
        print(f"Closed       : {tp_hit['percent']}%")
        print(f"Remaining    : {symbol_state['remaining_percent']}%")
        print(f"Trade PnL    : {round(symbol_state['trade_pnl'], 2)} USD")

        # =========================
        # BREAK EVEN
        # =========================

        if (
            symbol_state["breakeven_enabled"]
            and not symbol_state["breakeven_active"]
            and symbol_state["remaining_percent"] > 0
        ):

            symbol_state["sl"] = symbol_state["entry"]
            symbol_state["breakeven_active"] = True

            print("Break Even   : ON")

        send_tp_hit(
            symbol_state,
            tp_number,
            tp_hit,
            symbol_state["remaining_percent"],
            symbol_state["trade_pnl"],
            symbol_state["breakeven_active"]
        )

        # Ha ez volt az utolsó TP,
        # a maradék pozíció már 0.
        if symbol_state["remaining_percent"] <= 0:
            pass

        # Ha ez nem az utolsó TP, akkor marad nyitva a trade
        if symbol_state["remaining_percent"] > 0:

            # Trade továbbra is aktív.
            # Nem kereshet új belépőt.
            symbol_state["trade_active"] = True

            save_state(state)

        else:

            # Az utolsó TP után is mentsük el az állapotot,
            # mielőtt a végleges lezárás lefut.
            save_state(state)

        if symbol_state["remaining_percent"] > 0:

            print("Trade Status : ACTIVE")

            return False
     # =========================
    # FINAL CLOSE
    # =========================

    pnl = 0

    if result in ("LOSS", "BE"):

        pnl = calculate_pnl(
            entry,
            exit_price,
            symbol_state["pos_btc"],
            side
        )

        state["balance"] += pnl
        symbol_state["trade_pnl"] += pnl

    elif result == "WIN" and symbol_state["remaining_percent"] <= 0:

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

        loss_part = symbol_state["remaining_percent"] / 100.0

        state["losses"] += loss_part

    elif result == "BE":

        pass

    # =========================
    # FINAL TRADE CLOSE
    # =========================

    if symbol_state["remaining_percent"] <= 0 or result in ("LOSS", "BE"):

        state["total_trades"] += 1

        send_close(
            symbol_state,
            result,
            symbol_state["trade_pnl"],
            symbol_state.get("active_tf")
        )

        print(f"📉 TRADE CLOSED | {result}")

        close_trade(symbol_state, result)

        symbol_state["trade_active"] = False
        symbol_state["trade_side"] = None
        symbol_state["entry"] = 0
        symbol_state["sl"] = 0
        symbol_state["tp"] = 0
        symbol_state["pos_btc"] = 0
        symbol_state["pos_usd"] = 0
        symbol_state["initial_pos_btc"] = 0
        symbol_state["initial_pos_usd"] = 0
        symbol_state["remaining_percent"] = 0
        symbol_state["trade_pnl"] = 0.0
        symbol_state["breakeven_active"] = False
        symbol_state["entry_time"] = None
        symbol_state["entry_candle_close"] = None

        save_state(state)

        return True