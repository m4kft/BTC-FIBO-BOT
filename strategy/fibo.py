# strategy/fibo.py
#
# MEGJEGYZÉS: a korábbi build_fibo_context() függvényt eltávolítottuk
# innen - sehol nem volt meghívva, és duplikálta a
# strategy/zones.py -> get_zones() logikáját. A zóna-számítás
# egyetlen helyen (zones.py) él, hogy ne lehessen véletlenül
# csak az egyik verziót frissíteni.


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

    if level < 0.5:
        return None

    if side == "long":
        return high + ((level - 1.0) * range_size)

    if side == "short":
        return low - ((level - 1.0) * range_size)

    return None