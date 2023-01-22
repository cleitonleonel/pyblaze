import time
import toml
import requests
from datetime import datetime

config = toml.load('settings/config.toml')

host = config.get("server", "host")
port = config.get("server", "port")

URL_API = "https://blaze.com"
VERSION_API = "0.0.1-trial"
URL_HCAPTCHA_API = f"http://{host}:{port}"


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
        self.token = None
        self.hcaptcha_token = None
        self.is_logged = False
        self.wallet_id = None
        self.username = username
        self.password = password
        self.set_headers()
        self.headers = self.get_headers()

    def auth(self):
        data = {
            "username": self.username,
            "password": self.password
        }
        self.headers["x-captcha-response"] = self.hcaptcha_token or self.get_captcha_token()
        self.headers["referer"] = f"{URL_API}/pt/?modal=auth&tab=login"
        self.response = self.send_request("PUT",
                                          f"{URL_API}/api/auth/password",
                                          json=data,
                                          headers=self.headers)

        if not self.response.json().get("error"):
            self.token = self.response.json()["access_token"]
            self.is_logged = True
        return self.response.json()

    def reconnect(self):
        return self.auth()

    def hcaptcha_response(self):
        print("Using Anticaptcha System!!!")
        self.headers = self.get_headers()
        self.response = self.send_request("GET",
                                          f"{URL_HCAPTCHA_API}/hcaptcha/token",
                                          headers=self.headers)
        if self.response:
            return self.response.json().get("x-captcha-response")
        return None

    def get_captcha_token(self):
        response_result = self.hcaptcha_response()
        return response_result

    def get_profile(self):
        self.headers["authorization"] = f"Bearer {self.token}"
        self.response = self.send_request("GET",
                                          f"{URL_API}/api/users/me",
                                          headers=self.headers)
        if not self.response.json().get("error"):
            self.is_logged = True
        return self.response.json()

    def get_balance(self):
        self.headers["referer"] = f"{URL_API}/pt/games/double"
        self.headers["authorization"] = f"Bearer {self.token}"
        self.response = self.send_request("GET",
                                          f"{URL_API}/api/wallets",
                                          headers=self.headers)
        if self.response.status_code == 502:
            self.reconnect()
            return self.get_balance()
        elif self.response:
            self.wallet_id = self.response.json()[0]["id"]
        return self.response.json()

    def get_user_info(self):
        result_dict = {}
        result_dict["balance"] = self.get_balance()[0]["balance"]
        result_dict["username"] = self.get_profile()["username"]
        result_dict["wallet_id"] = self.get_balance()[0]["id"]
        result_dict["tax_id"] = self.get_profile()["tax_id"]
        return result_dict

    def get_status(self):
        self.response = self.get_roulettes()
        if self.response:
            return self.response.json()["status"]
        return {"status": "rolling"}

    def awaiting_result(self):
        while True:
            try:
                self.response = self.get_roulettes()
                print(f'\rSTATUS: {self.response.json()["status"]}', end="")
                if self.response.json()["status"] == "complete":
                    return self.response.json()
            except:
                pass
            time.sleep(0.1)

    def get_last_doubles(self):
        self.response = self.send_request("GET",
                                          f"{URL_API}/api/roulette_games/recent",
                                          proxies=self.proxies,
                                          headers=self.headers)
        if self.response:
            result = {
                "items": [
                    {"color": "branco" if i["color"] == 0 else "vermelho" if i["color"] == 1 else "preto",
                     "value": i["roll"], "created_date": datetime.strptime(
                        i["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
                     } for i in self.response.json()]}
            return result
        return False

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

    def get_roulettes(self):
        self.response = self.send_request("GET",
                                          f"{URL_API}/api/roulette_games/current",
                                          proxies=self.proxies,
                                          headers=self.headers)
        return self.response

    def double_bets(self, color, amount):
        result = False
        message = "Erro, aposta não concluída!!!"
        data = {
            "amount": float(f"{amount:.2f}"),
            "currency_type": "BRL",
            "color": 1 if color == "vermelho" else 2 if color == "preto" else 0,
            "free_bet": False,
            "wallet_id": self.wallet_id
        }

        self.headers["authorization"] = f"Bearer {self.token}"
        self.response = self.send_request("POST",
                                          f"{URL_API}/api/roulette_bets",
                                          json=data,
                                          headers=self.headers)
        if self.response:
            result = True
            message = "Operação realizada com sucesso!!!"

        return {
            "result": result,
            "object": self.response.json(),
            "message": message
        }
