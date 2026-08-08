# data/binance_ws.py
#
# Websocket-alapú, valós idejű candle adatréteg.
#
# CÉLJA: kiváltani a data/candles.py-ban lévő szinkron, blokkoló
# REST hívásokat a fő engine loop-ban - websocketen keresztül
# folyamatosan, push alapon kapjuk a gyertyaadatokat symbolonként
# és timeframe-enként, Spot és Futures piacra egyaránt.
#
# FONTOS - EZ AZ ÉLES HÁLÓZATI KAPCSOLATOT IGÉNYLŐ RÉSZ, amit
# a fejlesztői sandbox környezetben NEM lehetett élesben leteszt-
# elni (nincs kimenő hálózati hozzáférés). Az üzenet-feldolgozó
# logikát szimulált (mock) Binance üzenetekkel teszteltem - az
# üzenetformátum a Binance hivatalos websocket API dokumentáció-
# ját követi, de az élő kapcsolódást/újracsatlakozást neked kell
# majd valós környezetben kipróbálnod.
#
# A core/engine.py ÚGY használja ezt, hogy minden candle-lekérésnél
# ELŐSZÖR ezt próbálja (get_candle_ws) - ha nincs még adat, vagy
# elavult (STALE_SECONDS-nél régebbi), automatikusan visszaesik a
# meglévő, bevált REST hívásra (data/candles.py -> get_candle).
# Tehát ha a websocket bármiért nem működne élesben, a bot NEM áll
# le, csak lassabban (a régi módon) fog működni.

import json
import threading
import time

from state import state

# A "websocket" (websocket-client) csomagot szándékosan NEM itt,
# a fájl tetején importáljuk, hanem csak akkor, amikor ténylegesen
# kapcsolódni próbálunk (lásd _run_ws_forever). Így ez a modul
# akkor is importálható és tesztelhető marad (pl. a cache/parsing
# logika), ha a csomag esetleg hiányzik - és ha mégis hiányzik
# éles indításkor, egyértelmű hibaüzenetet kapsz, nem egy rejtett
# ImportError-t a teljes bot indításakor.
#
# Telepítés (ha még nincs meg):
#   pip install websocket-client --break-system-packages

# =========================
# BEÁLLÍTÁSOK
# =========================

SPOT_WS_URL = "wss://stream.binance.com:9443/ws"
FUTURES_WS_URL = "wss://fstream.binance.com/ws"

# Ha ennyi másodpercig nem jön adat egy symbol/timeframe streamre,
# elavultnak (stale) tekintjük, és a hívó félnek (engine.py) REST
# fallback-re kell váltania.
STALE_SECONDS = 30

# Reconnect várakozás: 2s-ról indul, duplázódik, max 60s-ig
RECONNECT_MIN_DELAY = 2
RECONNECT_MAX_DELAY = 60

# Feliratkozás-szinkronizálás gyakorisága (mp)
SUBSCRIPTION_SYNC_INTERVAL = 5


# =========================
# BELSŐ ÁLLAPOT
# =========================

_lock = threading.Lock()

# {(market, symbol, interval): {"current":..., "previous":..., "live":..., "last_update": ts}}
_cache = {}

# Az aktuálisan élő WebSocketApp példányok (market -> ws)
_ws_apps = {"spot": None, "futures": None}

# Amire ÉPPEN fel vagyunk iratkozva az adott kapcsolaton
_subscribed = {"spot": set(), "futures": set()}

_started = False


# =========================
# SEGÉDFÜGGVÉNYEK
# =========================

def _stream_name(symbol, interval):
    return f"{symbol.lower()}@kline_{interval}"


def _parse_kline(k):
    return {
        "open": float(k["o"]),
        "high": float(k["h"]),
        "low": float(k["l"]),
        "close": float(k["c"]),
        "timestamp": k["t"],
        "close_time": k["T"],
    }


def _handle_kline_message(market, data):
    """
    Egy bejövő kline websocket üzenetet dolgoz fel, és frissíti
    a belső cache-t. A várt üzenetformátum a Binance hivatalos
    kline stream dokumentációját követi:

    {
        "e": "kline",
        "s": "BTCUSDT",
        "k": {
            "t": <nyitás ts>, "T": <zárás ts>,
            "i": "5m",
            "o": "...", "h": "...", "l": "...", "c": "...",
            "x": true/false   <- lezárult-e a gyertya
        }
    }
    """

    try:
        k = data["k"]
        symbol = k["s"]
        interval = k["i"]

        candle = _parse_kline(k)

        key = (market, symbol, interval)

        with _lock:

            entry = _cache.get(key, {
                "current": None,
                "previous": None,
                "live": None,
                "last_update": 0,
            })

            if k.get("x"):
                # A gyertya lezárult - ez lesz az új "current",
                # a régi "current" pedig "previous"-á válik.
                entry["previous"] = entry["current"] if entry["current"] else candle
                entry["current"] = candle
                entry["live"] = candle  # legjobb becslés az új gyertya nyitásáig
            else:
                entry["live"] = candle

                # Ha még sosem kaptunk lezárt gyertyát erre a
                # symbol/interval-ra, ideiglenesen a live-ot
                # használjuk current/previous helyett is, hogy
                # a get_candle_ws() már az első üzenettől kezdve
                # tudjon valamit visszaadni.
                if entry["current"] is None:
                    entry["current"] = candle
                    entry["previous"] = candle

            entry["last_update"] = time.time()

            _cache[key] = entry

    except Exception as e:
        print(f"⚠ WS kline feldolgozási hiba ({market}): {e}")


# =========================
# WEBSOCKET CALLBACKEK
# =========================

def _make_on_message(market):

    def _on_message(ws, message):
        try:
            data = json.loads(message)

            # A "SUBSCRIBE"/"UNSUBSCRIBE" válaszüzenetek nem
            # tartalmaznak "k" kulcsot - ezeket kihagyjuk.
            if "k" in data:
                _handle_kline_message(market, data)

        except Exception as e:
            print(f"⚠ WS üzenet hiba ({market}): {e}")

    return _on_message


def _make_on_open(market):

    def _on_open(ws):
        print(f"✅ WS csatlakozva ({market})")

        # Újracsatlakozás után a korábban feliratkozott
        # streameket újra fel kell iratkoztatni.
        with _lock:
            streams = list(_subscribed[market])

        if streams:
            try:
                ws.send(json.dumps({
                    "method": "SUBSCRIBE",
                    "params": streams,
                    "id": 1
                }))
            except Exception as e:
                print(f"⚠ WS resubscribe hiba ({market}): {e}")

    return _on_open


def _on_error(ws, error):
    print(f"⚠ WS hiba: {error}")


def _on_close(ws, code, msg):
    print(f"WS lezárva: {code} {msg}")


# =========================
# KAPCSOLAT-KEZELŐ SZÁL (market-enként)
# =========================

def _run_ws_forever(market, url):

    try:
        import websocket
    except ImportError:
        print(
            "❌ HIÁNYZIK a 'websocket-client' csomag! "
            "Telepítsd: pip install websocket-client --break-system-packages\n"
            f"   A websocket adatréteg ({market}) emiatt nem tud elindulni - "
            "a bot a REST fallback-re fog támaszkodni."
        )
        return

    delay = RECONNECT_MIN_DELAY

    while True:

        try:
            ws = websocket.WebSocketApp(
                url,
                on_open=_make_on_open(market),
                on_message=_make_on_message(market),
                on_error=_on_error,
                on_close=_on_close,
            )

            _ws_apps[market] = ws

            # Sikeres kapcsolódás után visszaáll a reconnect delay
            delay = RECONNECT_MIN_DELAY

            ws.run_forever(ping_interval=180, ping_timeout=10)

        except Exception as e:
            print(f"⚠ WS EXCEPTION ({market}): {e}")

        _ws_apps[market] = None

        print(f"WS ({market}) újracsatlakozás {delay}s múlva...")
        time.sleep(delay)

        delay = min(delay * 2, RECONNECT_MAX_DELAY)


# =========================
# DINAMIKUS FELIRATKOZÁS-SZINKRONIZÁLÁS
# =========================

def _desired_streams():
    """
    A jelenlegi state["symbols"] alapján összeállítja, mely
    (market, stream) kombinációkra kellene feliratkozva lennünk.
    """

    desired = {"spot": set(), "futures": set()}

    for symbol, symbol_state in list(state.get("symbols", {}).items()):

        market = symbol_state.get("market", "spot")

        if market not in ("spot", "futures"):
            market = "spot"

        for tf in symbol_state.get("timeframes", []):
            desired[market].add(_stream_name(symbol, tf))

    return desired


def _sync_subscriptions_once():

    desired = _desired_streams()

    for market in ("spot", "futures"):

        ws = _ws_apps.get(market)

        if ws is None:
            # Nincs élő kapcsolat - a _make_on_open() úgyis
            # újra feliratkoztat majd csatlakozáskor, csak a
            # "kívánt" halmazt frissítjük.
            with _lock:
                _subscribed[market] = desired[market].copy() if not _subscribed[market] else _subscribed[market]
            continue

        with _lock:
            current = _subscribed[market].copy()

        to_add = desired[market] - current
        to_remove = current - desired[market]

        if to_add:
            try:
                ws.send(json.dumps({
                    "method": "SUBSCRIBE",
                    "params": list(to_add),
                    "id": 1
                }))
                with _lock:
                    _subscribed[market].update(to_add)
            except Exception as e:
                print(f"⚠ WS subscribe hiba ({market}): {e}")

        if to_remove:
            try:
                ws.send(json.dumps({
                    "method": "UNSUBSCRIBE",
                    "params": list(to_remove),
                    "id": 2
                }))
                with _lock:
                    _subscribed[market].difference_update(to_remove)
            except Exception as e:
                print(f"⚠ WS unsubscribe hiba ({market}): {e}")


def _subscription_supervisor():
    """
    Periodikusan ellenőrzi, hogy minden state["symbols"]-ben lévő
    symbol/timeframe fel van-e iratkozva - ha közben /add-oltál
    egy új symbolt, vagy módosítottad a /tf-et, ez automatikusan
    észreveszi, és feliratkozik rá - bot-újraindítás nélkül.
    """

    while True:

        try:
            _sync_subscriptions_once()
        except Exception as e:
            print(f"⚠ WS supervisor hiba: {e}")

        time.sleep(SUBSCRIPTION_SYNC_INTERVAL)


# =========================
# PUBLIKUS API
# =========================

def start_websocket():
    """
    Elindítja a Spot és Futures websocket kapcsolatokat (külön
    szálakon), plusz egy felügyelő szálat, ami folyamatosan
    frissíti a feliratkozásokat az aktuális state["symbols"]
    alapján.

    Csak egyszer indul el (idempotens) - ha main.py véletlenül
    kétszer hívná, nem indít duplán szálakat.
    """

    global _started

    if _started:
        return

    _started = True

    threading.Thread(
        target=_run_ws_forever,
        args=("spot", SPOT_WS_URL),
        daemon=True
    ).start()

    threading.Thread(
        target=_run_ws_forever,
        args=("futures", FUTURES_WS_URL),
        daemon=True
    ).start()

    threading.Thread(
        target=_subscription_supervisor,
        daemon=True
    ).start()

    print("🔌 Websocket adatréteg elindítva (spot + futures)")


def get_candle_ws(symbol, interval, market="spot"):
    """
    A websocket cache-ből próbálja visszaadni a candle adatot,
    PONTOSAN a REST get_candle() formátumával megegyezően:

    {
        "current": {...},
        "previous": {...},
        "live": {...}
    }

    Visszatér None-nal, ha:
    - még nincs adat erre a symbol/interval kombinációra
      (pl. most lett hozzáadva, még nem jött üzenet), VAGY
    - az utolsó frissítés túl régi (STALE_SECONDS-nél régebbi)

    Ilyenkor a hívó félnek (core/engine.py) REST fallback-re
    kell váltania - lásd data/candles.py -> get_candle().
    """

    if market not in ("spot", "futures"):
        market = "spot"

    key = (market, symbol, interval)

    with _lock:
        entry = _cache.get(key)

    if entry is None:
        return None

    if entry.get("current") is None or entry.get("live") is None:
        return None

    if time.time() - entry.get("last_update", 0) > STALE_SECONDS:
        return None

    return {
        "current": entry["current"],
        "previous": entry["previous"] or entry["current"],
        "live": entry["live"],
    }
