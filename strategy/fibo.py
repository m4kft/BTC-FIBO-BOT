# strategy/fibo.py


def build_fibo_context(high, low):
    """
    A user által megadott HIGH / LOW alapján
    kiszámolja a LONG és SHORT fibo szinteket + zónákat.

    Visszatér egy dict-tel, amiben minden benne van.
    """

    if high is None or low is None:
        return None

    range_size = high - low

    if range_size <= 0:
        return None

    # =========================
    # LONG FIBO
    # high -> low irányban mérve
    # =========================

    fibo_05 = high - (range_size * 0.5)
    fibo_0618 = high - (range_size * 0.618)
    fibo_0786 = high - (range_size * 0.786)

    long_zones = {
        "A": {
            "low": fibo_0618,
            "high": fibo_05
        },
        "B": {
            "low": fibo_0786,
            "high": fibo_0618
        },
        "C": {
            "low": low,
            "high": fibo_0786
        }
    }

    # =========================
    # SHORT FIBO
    # low -> high irányban mérve
    # =========================

    fibo_05_short = low + (range_size * 0.5)
    fibo_0618_short = low + (range_size * 0.618)
    fibo_0786_short = low + (range_size * 0.786)

    short_zones = {
        "A": {
            "low": fibo_05_short,
            "high": fibo_0618_short
        },
        "B": {
            "low": fibo_0618_short,
            "high": fibo_0786_short
        },
        "C": {
            "low": fibo_0786_short,
            "high": high
        }
    }

    return {
        "high": high,
        "low": low,
        "range_size": range_size,

        "long": {
            "fibo_05": fibo_05,
            "fibo_0618": fibo_0618,
            "fibo_0786": fibo_0786,
            "zones": long_zones
        },

        "short": {
            "fibo_05": fibo_05_short,
            "fibo_0618": fibo_0618_short,
            "fibo_0786": fibo_0786_short,
            "zones": short_zones
        }
    }


# ==========================================================
# FIBONACCI EXTENSION
# ==========================================================

def calculate_extension_price(side, high, low, level):
    """
    Fibonacci extension célár számítása.

    Long:
        1.0   = HIGH
        1.272 = HIGH felett
        1.618 = HIGH felett

    Short:
        1.0   = LOW
        1.272 = LOW alatt
        1.618 = LOW alatt
    """

    if high is None or low is None:
        return None

    range_size = high - low

    if range_size <= 0:
        return None

    try:
        level = float(level)
    except (TypeError, ValueError):
        return None

    if level < 1.0:
        return None

    if side == "long":
        return high + ((level - 1.0) * range_size)

    if side == "short":
        return low - ((level - 1.0) * range_size)

    return None