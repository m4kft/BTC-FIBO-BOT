def get_zones(high, low):

    """
    TradingView-kompatibilis fibo zónák
    LONG és SHORT külön számolva
    """

    if high is None or low is None:
        return None

    rng = high - low
    if rng <= 0:
        return None

    # =========================================================
    # 🟩 LONG (HIGH → LOW retrace)
    # 1 = LOW, 0 = HIGH (visszahúzás lefelé)
    # =========================================================
    fib_05 = high - rng * 0.5
    fib_0618 = high - rng * 0.618
    fib_0786 = high - rng * 0.786

    long_zones = {
        "A": {
            "low": fib_0618,
            "high": fib_05
        },
        "B": {
            "low": fib_0786,
            "high": fib_0618
        },
        "C": {
            "low": low,
            "high": fib_0786
        }
    }

    # =========================================================
    # 🟥 SHORT (LOW → HIGH retrace)
    # 1 = HIGH, 0 = LOW (visszahúzás felfelé)
    # =========================================================
    fib_05_s = low + rng * 0.5
    fib_0618_s = low + rng * 0.618
    fib_0786_s = low + rng * 0.786

    short_zones = {
        "A": {
            "low": fib_05_s,
            "high": fib_0618_s
        },
        "B": {
            "low": fib_0618_s,
            "high": fib_0786_s
        },
        "C": {
            "low": fib_0786_s,
            "high": high
        }
    }

    return {
        "high": high,
        "low": low,
        "range": rng,
        "long": long_zones,
        "short": short_zones
    }