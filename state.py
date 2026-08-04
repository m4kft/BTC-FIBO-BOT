from config import CONFIG
import json
import os

STATE_FILE = "state.json"


# =========================
# CORE STATE
# =========================
state = {
    # BOT CONTROL
    "running": True,

    # MARKET / SETUP
    "symbol": CONFIG["default_symbol"],
    "direction": CONFIG["default_direction"],
    "timeframes": CONFIG["default_timeframes"].copy(),

    # USER RANGE (FIBO)
    "high": None,
    "low": None,

    "range_set_time": 0,

    "structure_active": False,
    "range_invalid": False,

    # ACCOUNT / RISK
    "balance": CONFIG["paper_balance"],
    "risk": 1.0,

    # TRADE STATE
    "trade_active": False,
    "trade_side": None,

    "entry": 0.0,
    "sl": 0.0,
    "tp": 0.0,

    # TP SETTINGS
    "tp_level": 1.0,

    "entry_time": None,
    "entry_timeframe": None,
    "active_tf": None,

    "pos_btc": 0.0,
    "pos_usd": 0.0,

    # Eredeti pozíció mérete
    "initial_pos_btc": 0.0,
    "initial_pos_usd": 0.0,

    # =========================
    # V4 TRADE MANAGEMENT
    # =========================

    # Felhasználói TP beállítások
    # Ezeket Telegramból lehet majd módosítani.
    "tp_config": [
        {
            "type": "fibo",
            "value": 1.0,
            "percent": 100
        }
    ],

    # Az AKTUÁLIS trade célárai.
    # Trade nyitásakor a bot automatikusan felépíti
    # a tp_config alapján.
    "active_targets": [],

    # Mennyi pozíció maradt nyitva
    "remaining_percent": 100.0,

    # Break Even
    "breakeven_enabled": False,
    "breakeven_active": False,

    # Aktuális trade összesített PnL-je
    "trade_pnl": 0.0,

    # STATS
    "wins": 0.0,
    "losses": 0.0,
    "total_trades": 0,

    # SIGNAL
    "last_signal": None,
    "last_signal_tf": None,

    # CANDLE TRACKING
    "last_candle_ts": {
        "1m": None,
        "5m": None,
        "15m": None,
        "1h": None
    },

    # ZONES LOCK
    "long_zone_used": {
        "A": False,
        "B": False,
        "C": False
    },
    "short_zone_used": {
        "A": False,
        "B": False,
        "C": False
    }
}


# =========================
# LOAD STATE
# =========================
def load_state():

    if not os.path.exists(STATE_FILE):

        save_state(state)

        return state.copy()

    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}

    except:
        return {}

# =========================
# SAVE STATE (SAFE)
# =========================
def save_state(state_data):
    import time
    import os
    import json

    tmp_file = STATE_FILE + ".tmp"

    for _ in range(3):
        try:
            with open(tmp_file, "w") as f:
                json.dump(state_data, f, indent=4)

            os.replace(tmp_file, STATE_FILE)
            return

        except PermissionError:
            time.sleep(0.1)

        except Exception as e:
            print("SAVE ERROR:", e)
            return


# =========================
# RESET TRADE
# =========================
def reset_trade_state():

    # MARKET
    state["symbol"] = CONFIG["default_symbol"]
    state["direction"] = CONFIG["default_direction"]
    state["timeframes"] = CONFIG["default_timeframes"].copy()

    # RANGE
    state["high"] = None
    state["low"] = None
    state["range_set_time"] = 0
    state["structure_active"] = False
    state["range_invalid"] = False

    # TRADE
    state["trade_active"] = False
    state["trade_side"] = None

    state["entry"] = 0.0
    state["sl"] = 0.0
    state["tp"] = 0.0

    state["entry_time"] = None
    state["entry_timeframe"] = None
    state["active_tf"] = None

    state["pos_btc"] = 0.0
    state["pos_usd"] = 0.0

    state["initial_pos_btc"] = 0.0
    state["initial_pos_usd"] = 0.0

    # TAKE PROFIT
    state["tp_level"] = 1.0

    state["tp_config"] = [
        {
            "type": "fibo",
            "value": 1.0,
            "percent": 100
        }
    ]

    state["active_targets"] = []
    state["remaining_percent"] = 100.0

    # BREAK EVEN
    state["breakeven_enabled"] = False
    state["breakeven_active"] = False

    # SIGNAL
    state["last_signal"] = None
    state["last_signal_tf"] = None

    # CANDLES
    state["last_candle_ts"] = {
        "1m": None,
        "5m": None,
        "15m": None,
        "1h": None
    }

    # ZONE LOCK
    state["long_zone_used"] = {
        "A": False,
        "B": False,
        "C": False
    }

    state["short_zone_used"] = {
        "A": False,
        "B": False,
        "C": False
    }

# =========================
# FACTORY RESET
# =========================
def factory_reset_state():

    reset_trade_state()

    state["balance"] = CONFIG["paper_balance"]
    state["risk"] = 1.0

    state["wins"] = 0.0
    state["losses"] = 0.0
    state["total_trades"] = 0

    state["trade_pnl"] = 0.0