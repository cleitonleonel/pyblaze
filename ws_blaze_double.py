import websocket
import _thread
import json
import time


WSS_BASE = "wss://api-v2.blaze.com"


def get_color(number):
    colors = {
        0: "branco",
        1: "vermelho",
        2: "preto"
    }
    return colors.get(number, )


def on_message(ws, message):
    global length
    if "double.tick" in message:
        data = json.loads(message[2:])[1]["payload"]
        if data["status"] == "complete" and length != len(message) + 1:
            length = len(message) + 1
            print(fr'Giro anterior {data["roll"]}, cor {get_color(data["color"])}')


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
        message = '%d["cmd", {"id": "subscribe", "payload": {"room": "double_v2"}}]' % 421
        ws.send(message)
        time.sleep(0.1)
        message = '%d["cmd", {"id": "subscribe", "payload": {"room": "chat_room_2"}}]' % 422
        ws.send(message)
        print('connection established')

    _thread.start_new_thread(run, ())


def connect_websocket():
    # websocket.enableTrace(True)
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
