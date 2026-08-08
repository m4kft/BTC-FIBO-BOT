from config import CONFIG
import json
import os

STATE_FILE = "state.json"

# =========================
# SYMBOL INPUT NORMALIZÁLÁS
# =========================
def normalize_symbol_input(raw_symbol):
    """
    Bemeneti symbol string normalizálása.

    Felismeri a TradingView-stílusú ".P" jelölést
    (pl. "GWEIUSDT.P"), ami perpetual futures kontraktust
    jelent - ilyenkor a ".P"-t levágjuk, és a piacot
    "futures"-re állítjuk.

    Enélkül (pl. "BTCUSDT") a piac "spot" marad - ez a
    korábbi, megszokott viselkedés, visszafelé kompatibilis.

    Visszatér: (clean_symbol, market)
    market: "spot" vagy "futures"
    """

    raw = raw_symbol.strip().upper()

    if raw.endswith(".P"):
        return raw[:-2], "futures"

    return raw, "spot"


# =========================
# SYMBOL TEMPLATE
# =========================
def create_symbol_state():

    return {

        # MARKET
        "symbol": CONFIG["default_symbol"],
        "market": "spot",  # "spot" vagy "futures" - lásd normalize_symbol_input()
        "direction": CONFIG["default_direction"],
        "timeframes": CONFIG["default_timeframes"].copy(),

        # RANGE
        "high": None,
        "low": None,

        "price_precision": 2,

        "range_set_time": 0,

        "structure_active": False,
        "range_invalid": False,

        # TRADE
        "trade_active": False,
        "trade_side": None,

        "entry": 0.0,
        "sl": 0.0,
        "tp": 0.0,

        "entry_time": None,
        "entry_timeframe": None,
        "active_tf": None,
        "entry_candle_close": None,

        "pos_btc": 0.0,
        "pos_usd": 0.0,

        "initial_pos_btc": 0.0,
        "initial_pos_usd": 0.0,

        # TP
        "tp_level": 1.0,

        "tp_config": [
            {
                "type": "fibo",
                "value": 1.0,
                "percent": 100
            }
        ],

        "active_targets": [],
        "remaining_percent": 100.0,

        # BREAK EVEN
        "breakeven_enabled": False,
        "breakeven_active": False,

        "trade_pnl": 0.0,

        # SIGNAL
        "last_signal": None,
        "last_signal_tf": None,

        # CANDLES
        "last_candle_ts": {
            "1m": None,
            "5m": None,
            "15m": None,
            "1h": None
        },

        # ZONE LOCK
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
# CORE STATE
# =========================
state = {

    # =========================
    # BOT CONTROL
    # =========================
    "running": True,

    # =========================
    # GLOBAL ACCOUNT
    # =========================
    "balance": CONFIG["paper_balance"],
    "risk": 1.0,

    "wins": 0.0,
    "losses": 0.0,
    "total_trades": 0,

    # =========================
    # ACTIVE SYMBOL
    # =========================
    "active_symbol": CONFIG["default_symbol"],

    # =========================
    # SYMBOLS
    # =========================
    "symbols": {
        CONFIG["default_symbol"]: create_symbol_state()
    },

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
# INITIALIZE STATE (EXPLICIT)
# =========================
def initialize_state():
    """
    Ezt kell meghívni induláskor, MIELŐTT bármi mást csinálunk
    (engine indítás, recovery, stb.) - explicit, jól látható
    módon tölti be a state.json-t, ahelyett hogy egy import
    mellékhatásaként történne (ami törékeny: import sorrend
    változtatásra elromlana).

    Emellett minden symbol állapotot összefésül a
    create_symbol_state() sablonnal, így ha a kód időközben
    új mezőt vezetett be, a régi, mentett state.json-ban
    hiányzó mezők automatikusan pótlódnak alapértelmezett
    értékkel - nem lesz belőle KeyError.
    """

    loaded = load_state()

    if not loaded:
        print("📦 STATE: nincs korábbi mentés, alapértelmezett állapot marad.")
        return state

    state.update(loaded)

    # Séma-migráció: minden symbolnál pótoljuk a hiányzó mezőket
    template = create_symbol_state()

    for symbol, symbol_state in state.get("symbols", {}).items():
        for key, default_value in template.items():
            if key not in symbol_state:
                print(f"🔧 STATE MIGRATION: '{symbol}' - hiányzó mező pótolva: '{key}'")
                symbol_state[key] = default_value

    print("📦 STATE LOADED (initialize_state)")

    return state

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

    # =========================
    # V5 MULTI SYMBOL RESET
    # =========================

    for symbol_state in state["symbols"].values():

        symbol_state["trade_active"] = False
        symbol_state["trade_side"] = None

        symbol_state["entry"] = 0.0
        symbol_state["sl"] = 0.0
        symbol_state["tp"] = 0.0

        symbol_state["entry_time"] = None
        symbol_state["entry_timeframe"] = None
        symbol_state["active_tf"] = None

        symbol_state["pos_btc"] = 0.0
        symbol_state["pos_usd"] = 0.0

        symbol_state["initial_pos_btc"] = 0.0
        symbol_state["initial_pos_usd"] = 0.0

        symbol_state["active_targets"] = []
        symbol_state["remaining_percent"] = 100.0

        symbol_state["trade_pnl"] = 0.0

        symbol_state["breakeven_active"] = False

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

    # =========================
    # V5 RANGE RESET
    # =========================

    for symbol_state in state["symbols"].values():

        symbol_state["high"] = None
        symbol_state["low"] = None

        symbol_state["range_set_time"] = 0

        symbol_state["structure_active"] = False
        symbol_state["range_invalid"] = False

        symbol_state["long_zone_used"] = {
            "A": False,
            "B": False,
            "C": False
        }

        symbol_state["short_zone_used"] = {
            "A": False,
            "B": False,
            "C": False
        }

    state["balance"] = CONFIG["paper_balance"]
    state["risk"] = 1.0

    state["wins"] = 0.0
    state["losses"] = 0.0
    state["total_trades"] = 0

    state["trade_pnl"] = 0.0