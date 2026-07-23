from state import state, save_state
from data.candles import get_candles_since
from execution.trade_exit import check_trade_exit
from telegram.bot import send_message

def recover_trade():

    print("🔄 Offline Recovery...")

    if not state["trade_active"]:
        print("✅ No active trade.")
        return

    print("📌 Active trade found.")

    if state.get("entry_candle_close") is None:
        print("⚠ No entry_candle_close found.")
        return

    candles = get_candles_since(
        interval=state["active_tf"],
        start_time=state["entry_candle_close"]
    )

    print(f"📊 Missed candles: {len(candles)}")

    for candle in candles:
       
        if check_trade_exit(candle):

            print("✅ Offline trade recovered.")
            break

    if state["trade_active"]:
        print("ℹ️ Trade still active after recovery.")


def recover_range():

    print("🔍 Offline Range Recovery...")

    if not state["structure_active"]:
        print("ℹ️ No active range.")
        return

    if state.get("range_set_time") is None or state["range_set_time"] == 0:
        print("⚠ No range_set_time found.")
        return

    candles = get_candles_since(
        interval="5m",
        start_time=state["range_set_time"]
    )

    print(f"📊 Checking {len(candles)} candles...")

    for candle in candles:

        if candle["high"] > state["high"] or candle["low"] < state["low"]:

            print("❌ Range was broken while bot was offline!")

            state["structure_active"] = False
            state["range_invalid"] = True

            save_state(state)

            try:
                send_message("❌ RANGE INVALID (Offline Recovery)")
            except:
                pass

            return

    print("✅ Range still valid.")