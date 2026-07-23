# execution/risk.py

def calculate_position_size(balance, risk_percent, entry, sl):
    """
    Megmondja, mekkora pozíciót nyithatsz.
    """

    risk_amount = balance * (risk_percent / 100)

    stop_distance = abs(entry - sl)

    if stop_distance == 0:
        return 0, 0

    pos_size = risk_amount / stop_distance
    position_value = pos_size * entry

    return pos_size, position_value