import websocket
import _thread
import time
import json

WSS_BASE = "wss://api-v2.blaze.com"


def on_message(ws, message):
    global length
    if "crash.tick" in message:
        data = json.loads(message[2:])[1]["payload"]
        if data["status"] == "complete" and length != len(message):
            length = len(message)
            print(f'\rCrash Point: {data["crash_point"]}, cor {"verde" if float(data["crash_point"]) > 2 else "preto"}')
            if data["crash_point"] == "0" or data["crash_point"].endswith('.00') or float(data["crash_point"]) > 49:
                print("\nPOSSÍVEL BRANCO NO DOUBLE...")


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    time.sleep(2)
    connect_websocket()


def on_ping(ws, message):
    print("Got a ping! A pong reply has already been automatically sent.")


def on_pong(ws, message):
    ws.send("2")


def on_open(ws):
    def run(*args):
        time.sleep(1)
        message = '%d["cmd", {"id": "subscribe", "payload": {"room": "crash_v2"}}]' % 420
        ws.send(message)
        time.sleep(0.1)
        message = '%d["cmd", {"id": "subscribe", "payload": {"room": "chat_room_2"}}]' % 422
        ws.send(message)
        print('connection established')

    _thread.start_new_thread(run, ())


def connect_websocket():
    ws = websocket.WebSocketApp(f"{WSS_BASE}/replication/?EIO=3&transport=websocket",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_ping=on_ping,
                                on_pong=on_pong
                                )

    ws.run_forever(ping_interval=24, ping_timeout=1, ping_payload="2")


if __name__ == "__main__":
    length = 0
    try:
        connect_websocket()
    except Exception as err:
        print(err)
        print("connect failed")
