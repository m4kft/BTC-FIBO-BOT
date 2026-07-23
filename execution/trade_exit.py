from state import state, save_state
from execution.pnl import calculate_pnl
from execution.paper import close_trade
from telegram.bot import send_close


def check_trade_exit(candle):

    if not state["trade_active"]:
        return False

    side = state["trade_side"]
    entry = state["entry"]
    sl = state["sl"]
    tp = state["tp"]
    pos_btc = state["pos_btc"]

    high = candle["high"]
    low = candle["low"]

    result = None
    exit_price = None

    # LONG EXIT
    if side == "long":
        if low <= sl:
            result = "LOSS"
            exit_price = sl
        elif high >= tp:
            result = "WIN"
            exit_price = tp

    # SHORT EXIT
    elif side == "short":
        if high >= sl:
            result = "LOSS"
            exit_price = sl
        elif low <= tp:
            result = "WIN"
            exit_price = tp

    if result is None:
        return False

    pnl = calculate_pnl(entry, exit_price, pos_btc, side)

    state["balance"] += pnl

    if result == "WIN":
        state["wins"] += 1
    else:
        state["losses"] += 1

    state["total_trades"] += 1

    send_close(result, pnl, state.get("active_tf"))

    print(f"📉 TRADE CLOSED | {result} | PnL: {round(pnl, 2)}")

    close_trade(result)

    state["trade_active"] = False
    state["trade_side"] = None
    state["entry"] = 0
    state["sl"] = 0
    state["tp"] = 0
    state["pos_btc"] = 0
    state["pos_usd"] = 0
    state["entry_time"] = None
    state["entry_candle_close"] = None
    save_state(state)

    return True