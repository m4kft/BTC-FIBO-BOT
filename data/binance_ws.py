import websocket
import json
import time

current_price = None


def get_current_price():
    return current_price


def on_message(ws, message):
    global current_price

    data = json.loads(message)

    current_price = float(data["p"])

    print("BTC:", current_price)


def on_open(ws):
    print("✅ Connected")


def on_error(ws, error):
    print("ERROR:", error)


def on_close(ws, close_status_code, close_msg):
    print("Closed")


def start_websocket():

    while True:

        try:

            socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"

            ws = websocket.WebSocketApp(
                socket,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )

            ws.run_forever()

        except Exception as e:
            print("WS EXCEPTION:", e)

        print("Reconnect 5 sec...")
        time.sleep(5)