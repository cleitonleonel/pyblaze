import websocket
import _thread
import time
import json

WSS_BASE = "wss://api-v2.blaze.com"


def get_color(number):
    colors = {
        0: "branco",
        1: "vermelho",
        2: "preto"
    }
    return colors.get(number, )


def on_message(ws, message):
    if "roulette.update" in message:
        data = json.loads(message[2:])[1]["payload"]
        if data["status"] == "complete":
            print(fr'Giro anterior {data["roll"]}, cor {get_color(data["color"])}')

        ws.send('2')


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    count_bet = 0

    def run(*args):
        time.sleep(1)
        message = '%d["cmd", {"id": "subscribe", "payload": {"room": "roulette"}}]' % 420
        ws.send(message)
        time.sleep(0.1)
        message = '%d["cmd", {"id": "subscribe", "payload": {"room": "chat_room_2"}}]' % 421
        ws.send(message)

    _thread.start_new_thread(run, ())


if __name__ == "__main__":
    # websocket.enableTrace(True)

    ws = websocket.WebSocketApp(f"{WSS_BASE}/replication/?EIO=3&transport=websocket",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close
                                )

    ws.run_forever()
