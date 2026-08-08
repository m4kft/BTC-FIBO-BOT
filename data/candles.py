# data/candles.py

import requests
import time
from state import state

BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"


def resolve_binance_url(symbol):
    """
    Symbolonként eldönti, hogy Spot vagy Futures (USDⓈ-M perpetual)
    Binance végpontot kell-e hívni, a state.py-ban tárolt
    "market" mező alapján (lásd normalize_symbol_input()).

    Ha a symbol nem szerepel a state["symbols"]-ben (pl. egy
    régi/külső hívás), alapértelmezésként "spot"-ot használunk -
    ez a korábbi, megszokott viselkedés, visszafelé kompatibilis.
    """

    symbol_state = state.get("symbols", {}).get(symbol)

    market = symbol_state.get("market", "spot") if symbol_state else "spot"

    if market == "futures":
        return BINANCE_FUTURES_URL

    return BINANCE_SPOT_URL


def get_candle(symbol=None, interval="5m", limit=3):
    """
    Binance gyertyák lekérése.

    Ha nincs megadva symbol → state["symbol"]-t használja.

    Visszaad:
    {
        "previous": {...},
        "current": {...}
    }
    """

    # =========================
    # SYMBOL SAFE LOGIKA
    # =========================
    if symbol is None:
        symbol = state["symbol"]

    binance_url = resolve_binance_url(symbol)

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    # =========================
    # BINANCE REQUEST (RETRY)
    # =========================
    last_error = None

    for attempt in range(3):

        try:

            response = requests.get(
                binance_url,
                params=params,
                timeout=5
            )

            response.raise_for_status()

            data = response.json()

            break

        except requests.exceptions.RequestException as e:

            last_error = e

            print(f"⚠ Binance request failed ({attempt + 1}/3): {e}")

            time.sleep(1)

    else:
        raise Exception(f"Binance request failed after 3 attempts: {last_error}")

    # Biztonsági ellenőrzés
    if not isinstance(data, list) or len(data) < 3:
        raise Exception(f"Hibás Binance candle válasz: {data}")

    # =========================
    # BINANCE CANDLES
    # =========================
    prev = data[-3]
    curr = data[-2]

    return {
        "current": {
            "open": float(curr[1]),
            "high": float(curr[2]),
            "low": float(curr[3]),
            "close": float(curr[4]),
            "timestamp": curr[0],
            "close_time": curr[6]
        },
        "previous": {
            "open": float(prev[1]),
            "high": float(prev[2]),
            "low": float(prev[3]),
            "close": float(prev[4]),
            "timestamp": prev[0],
            "close_time": prev[6]
        },
        "live": {
            "open": float(data[-1][1]),
            "high": float(data[-1][2]),
            "low": float(data[-1][3]),
            "close": float(data[-1][4]),
            "timestamp": data[-1][0],
            "close_time": data[-1][6]
        }

    }

def get_candles_since(symbol=None, interval="5m", start_time=None, limit=1000):
    """
    Lekéri az összes lezárt gyertyát egy adott időponttól.
    Offline Recovery használja.
    """

    if symbol is None:
        symbol = state["symbol"]

    binance_url = resolve_binance_url(symbol)

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "limit": limit
    }

    last_error = None

    for attempt in range(3):

        try:

            response = requests.get(
                binance_url,
                params=params,
                timeout=5
            )

            response.raise_for_status()

            data = response.json()

            break

        except requests.exceptions.RequestException as e:

            last_error = e

            print(f"⚠ Binance request failed ({attempt + 1}/3): {e}")

            time.sleep(1)

    else:
        raise Exception(f"Binance request failed after 3 attempts: {last_error}")

    if not isinstance(data, list):
        raise Exception(f"Hibás Binance candle válasz: {data}")

    candles = []

    # Az utolsó gyertya még nyitott lehet, ezért kihagyjuk
    for c in data[:-1]:

        candles.append({
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "timestamp": c[0],
            "close_time": c[6]
        })

    return candles