def is_hammer(o, h, l, c):
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    return lower >= body * 2 and upper <= lower * 0.3


def is_shooting_star(o, h, l, c):
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    return upper >= body * 2 and lower <= upper * 0.3


def is_bullish_engulfing(po, pc, co, c):
    return pc < po and c > co and co <= pc and c >= po


def is_bearish_engulfing(po, pc, co, c):
    return pc > po and c < co and co >= pc and c <= po