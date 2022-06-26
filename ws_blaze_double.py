import time
import json
import requests
import websocket
from datetime import datetime

URL_API = "https://blaze.com"
WSS_BASE = "wss://api-v2.blaze.com"
VERSION_API = "0.0.1-professional"

close_ws = False
result_dict = None
updated_at = None
last_doubles = []


def get_ws_result():
    return result_dict


def set_ws_closed(status):
    global close_ws
    close_ws = status


def get_doubles():
    doubles = ba.get_last_doubles()
    if doubles:
        return [[item["value"], item["color"]] for item in doubles["items"]][::-1]


def roulette_preview():
    global last_doubles
    last_doubles = last_doubles[1:]
    colored_string = ', '.join([
        f"\033[10;40m {item[0]} \033[m" if item[1] == "preto"
        else f"\033[10;41m {item[0]} \033[m" if item[1] == "vermelho"
        else f"\033[10;47m {item[0]} \033[m" for item in last_doubles])
    print(f"\r{colored_string}", end="")


def get_color(number):
    colors = {
        0: "branco",
        1: "vermelho",
        2: "preto"
    }
    return colors.get(number, None)


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = None
        self.session = requests.Session()

    def set_headers(self, headers=None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        if headers:
            for key, value in headers.items():
                self.headers[key] = value

    def get_headers(self):
        return self.headers

    def send_request(self, method, url, **kwargs):
        return self.session.request(method, url, **kwargs)


class BlazeAPI(Browser):

    def __init__(self, username=None, password=None):
        super().__init__()
        self.proxies = None
        self.username = username
        self.password = password
        self.set_headers()
        self.headers = self.get_headers()

    def get_last_doubles(self):
        self.response = self.send_request("GET",
                                          f"{URL_API}/api/roulette_games/recent",
                                          proxies=self.proxies,
                                          headers=self.headers)
        if self.response:
            result_double = {
                "items": [
                    {"color": "branco" if i["color"] == 0 else "vermelho" if i["color"] == 1 else "preto",
                     "value": i["roll"], "created_date": datetime.strptime(
                        i["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
                     } for i in self.response.json()]}
            return result_double

        return False


def on_message(ws, msg):
    global result_dict
    global close_ws
    global updated_at
    global last_doubles
    if "double.tick" in msg:
        result_dict = json.loads(msg[2:])[1]["payload"]
        if result_dict["status"] == "rolling" and updated_at != result_dict["updated_at"]:
            updated_at = result_dict["updated_at"]
            last_doubles.append([result_dict["roll"], get_color(result_dict["color"])])
            roulette_preview()

    if close_ws:
        ws.close()


def on_close(ws, status, msg):
    time.sleep(1)
    connect_websocket()


def on_pong(ws, msg):
    ws.send("2")


def on_open(ws):
    global last_doubles
    message = '%d["cmd", {"id": "subscribe", "payload": {"room": "double_v2"}}]' % 421
    ws.send(message)
    last_doubles = get_doubles()


def connect_websocket():
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f"{WSS_BASE}/replication/?EIO=3&transport=websocket",
                                header=ba.headers,
                                on_open=on_open,
                                on_message=on_message,
                                on_close=on_close,
                                on_pong=on_pong
                                )

    ws.run_forever(ping_interval=24,
                   ping_timeout=5,
                   ping_payload="2",
                   origin="https://blaze.com",
                   host="api-v2.blaze.com")


ba = BlazeAPI()

connect_websocket()
