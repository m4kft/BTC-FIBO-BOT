def calculate_pnl(entry, exit_price, pos_size, side):
    if side == "long":
        return (exit_price - entry) * pos_size
    else:
        return (entry - exit_price) * pos_size