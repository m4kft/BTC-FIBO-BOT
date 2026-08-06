from state import state, save_state
from data.candles import get_candles_since
from execution.trade_exit import check_trade_exit
from telegram.bot import send_message


def recover_trade():

    print("🔄 Offline Recovery...")

    for symbol, symbol_state in state["symbols"].items():

        if not symbol_state["trade_active"]:
            continue

        print(f"📌 Active trade found: {symbol}")

        if symbol_state.get("entry_candle_close") is None:
            print(f"⚠ {symbol}: No entry_candle_close found.")
            continue

        candles = get_candles_since(
            symbol=symbol,
            interval=symbol_state["active_tf"],
            start_time=symbol_state["entry_candle_close"]
        )

        print(f"📊 {symbol} | Missed candles: {len(candles)}")

        for candle in candles:

            if check_trade_exit(symbol_state, candle):

                print(f"✅ {symbol} | Offline trade recovered.")
                break

        if symbol_state["trade_active"]:
            print(f"ℹ️ {symbol} | Trade still active after recovery.")


def recover_range():

    print("🔍 Offline Range Recovery...")

    for symbol, symbol_state in state["symbols"].items():

        if not symbol_state["structure_active"]:
            continue

        if (
            symbol_state.get("range_set_time") is None
            or symbol_state["range_set_time"] == 0
        ):
            print(f"⚠ {symbol}: No range_set_time found.")
            continue

        candles = get_candles_since(
            symbol=symbol,
            interval="5m",
            start_time=symbol_state["range_set_time"]
        )

        print(f"📊 {symbol} | Checking {len(candles)} candles...")

        for candle in candles:

            if (
                candle["high"] > symbol_state["high"]
                or candle["low"] < symbol_state["low"]
            ):

                print(f"❌ {symbol} | Range was broken while bot was offline!")

                symbol_state["structure_active"] = False
                symbol_state["range_invalid"] = True

                save_state(state)

                try:
                    send_message(
                        f"❌ {symbol}\n"
                        "Range invalid (Offline Recovery)"
                    )
                except:
                    pass

                break

        else:
            print(f"✅ {symbol} | Range still valid.")