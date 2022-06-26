import requests
import websocket
import time
import json

URL_API = "https://blaze.com"
WSS_BASE = "wss://api-v2.blaze.com"
VERSION_API = "0.0.1-professional"

close_ws = False
result_dict = None
updated_at = None
last_crashs = []


def get_ws_result():
    return result_dict


def set_ws_closed(status):
    global close_ws
    close_ws = status


def get_crashs():
    doubles = ba.get_last_crashs()
    if doubles:
        return [[item["value"], item["color"]] for item in doubles["items"]][::-1]


def crashs_preview():
    global last_crashs
    last_crashs = last_crashs[1:]
    colored_string = ', '.join([
        f"\033[10;40m {item[0]} \033[m" if item[1] == "preto"
        else f"\033[10;42m {item[0]} \033[m" for item in last_crashs])
    print(f"\r{colored_string}", end="")


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

    def get_last_crashs(self):
        self.response = self.send_request("GET",
                                          f"{URL_API}/api/crash_games/recent",
                                          proxies=self.proxies,
                                          headers=self.headers)
        if self.response:
            result = {
                "items": [{"color": "preto" if float(i["crash_point"]) < 2 else "verde", "value": i["crash_point"]}
                          for i in self.response.json()]}
            return result
        return False


def on_message(ws, message):
    global result_dict
    global close_ws
    global updated_at
    global last_crashs
    if "crash.tick" in message:
        result_dict = json.loads(message[2:])[1]["payload"]
        if result_dict["status"] == "complete" and updated_at != result_dict["updated_at"]:
            updated_at = result_dict["updated_at"]
            last_crashs.append([result_dict["crash_point"],
                                "verde" if float(result_dict["crash_point"]) > 2 else "preto"])
            crashs_preview()


def on_error(ws, error):
    print(error)


def on_close(ws, status, msg):
    time.sleep(1)
    connect_websocket()


def on_pong(ws, msg):
    ws.send("2")


def on_open(ws):
    global last_crashs
    message = '%d["cmd", {"id": "subscribe", "payload": {"room": "crash_v2"}}]' % 420
    ws.send(message)
    last_crashs = get_crashs()


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
