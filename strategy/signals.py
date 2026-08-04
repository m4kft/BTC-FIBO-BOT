from strategy.patterns import (
    is_hammer,
    is_shooting_star,
    is_bullish_engulfing,
    is_bearish_engulfing
)


# =========================
# LONG ZÓNA DETECT
# =========================
def get_active_long_zone(close_price, zones):
    for zone_name, zone in zones["long"].items():
        if zone["low"] <= close_price <= zone["high"]:
            return zone_name
    return None


# =========================
# SHORT ZÓNA DETECT
# =========================
def get_active_short_zone(close_price, zones):
    for zone_name, zone in zones["short"].items():
        if zone["low"] <= close_price <= zone["high"]:
            return zone_name
    return None


# =========================
# LONG SIGNAL
# =========================
def get_long_signal(candle, prev_candle, zones, state):

    if state["direction"] != "long":
        return None

    o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
    po, pc = prev_candle["open"], prev_candle["close"]

    hammer = is_hammer(o, h, l, c)
    bullish_engulfing = is_bullish_engulfing(po, pc, o, c)

    if not (hammer or bullish_engulfing):
        return None

    # LONG 0.5 filter
    fibo_05 = zones["long"]["A"]["high"]  # kb 0.5 szint
    if c >= fibo_05:
        return None

    print("\n----- LONG CHECK -----")
    print(f"Close: {c}")
    print(f"0.5 level: {fibo_05}")
    print(f"Detected zone: {get_active_long_zone(c, zones)}")

    zone = get_active_long_zone(c, zones)
    if zone is None:
        return None

    if state["long_zone_used"][zone]:
        return None

    pattern = "HAMMER" if hammer else "BULLISH_ENGULFING"

    return {
        "side": "long",
        "zone": zone,
        "pattern": pattern,
        "entry_price": c
    }


# =========================
# SHORT SIGNAL
# =========================
def get_short_signal(candle, prev_candle, zones, state):

    if state["direction"] != "short":
        return None

    o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
    po, pc = prev_candle["open"], prev_candle["close"]

    shooting_star = is_shooting_star(o, h, l, c)
    bearish_engulfing = is_bearish_engulfing(po, pc, o, c)

    if not (shooting_star or bearish_engulfing):
        return None

    # SHORT 0.5 filter
    fibo_05 = zones["short"]["A"]["low"]
    if c <= fibo_05:
        return None

    print("\n----- SHORT CHECK -----")
    print(f"Close: {c}")
    print(f"0.5 level: {fibo_05}")
    print(f"Detected zone: {get_active_short_zone(c, zones)}")

    zone = get_active_short_zone(c, zones)
    if zone is None:
        return None

    if state["short_zone_used"][zone]:
        return None

    pattern = "SHOOTING_STAR" if shooting_star else "BEARISH_ENGULFING"

    return {
        "side": "short",
        "zone": zone,
        "pattern": pattern,
        "entry_price": c
    }


# =========================
# MAIN SIGNAL
# =========================
def get_signal(candle, prev_candle, zones, state):

    long_signal = get_long_signal(candle, prev_candle, zones, state)
    if long_signal:
        return long_signal

    short_signal = get_short_signal(candle, prev_candle, zones, state)
    if short_signal:
        return short_signal

    return None