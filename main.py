from state import state
from core.engine import run_engine
from telegram.runner import run_telegram_listener
from execution.recovery import recover_trade, recover_range
import threading


def setup_test_values():

    state["running"] = True
    state["symbol"] = "BTCUSDT"
    state["direction"] = "short"

    state["high"] = 60400.0
    state["low"] = 58110.0

    state["risk"] = 1.0

    print("✅ TEST VALUES LOADED")
    print("Symbol:", state["symbol"])
    print("Direction:", state["direction"])
    print("High:", state["high"])
    print("Low:", state["low"])
    print("Risk:", state["risk"])


if __name__ == "__main__":

    # =========================
    # OFFLINE RECOVERY
    # =========================
    recover_trade()
    recover_range()

    # =========================
    # ENGINE THREAD
    # =========================
    t1 = threading.Thread(target=run_engine)

    # =========================
    # TELEGRAM CONTROL THREAD
    # =========================
    t2 = threading.Thread(target=run_telegram_listener)

    t1.start()
    t2.start()

    t1.join()
    t2.join()