# core/context.py

from data.candles import get_candle
from state import state


def build_context(timeframe: str):
    """
    Ez összerakja a bot "pillanatnyi képét".
    Ezt kapja a strategy engine.
    """

    symbol = state["symbol"]

    candle = get_candle(symbol, timeframe)

    prev_candle = candle["previous"]

    context = {
        "symbol": symbol,
        "timeframe": timeframe,

        # aktuális gyertya
        "candle": candle["current"],

        # előző gyertya
        "prev_candle": prev_candle,

        # state (teljes bot állapot)
        "state": state
    }

    return context