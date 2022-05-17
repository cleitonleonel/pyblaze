import time
import requests
from datetime import datetime

URL_API = "https://blaze.com"
URL_WEB_PROXY = "https://us13.proxysite.com"
VERSION_API = "0.0.1-trial"


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

    def get_status(self):
        self.response = self.get_roulettes()
        if self.response:
            return self.response.json()["status"]
        return {"status": "rolling"}

    def get_ranking(self, **params):
        list_best_users = []
        while True:
            self.response = self.get_roulettes()
            if self.response:
                if self.response.json()["status"] == 'waiting':
                    for user_rank in self.response.json()["bets"]:
                        if user_rank["user"]["rank"] in params["ranks"]:
                            list_best_users.append(user_rank)
                    return list_best_users
            time.sleep(2)

    def get_trends(self):
        while True:
            self.response = self.get_roulettes()
            if self.response:
                if self.response.json()["status"] == 'waiting':
                    return self.response.json()
            time.sleep(2)

    def awaiting_result(self):
        while True:
            try:
                self.response = self.get_roulettes()

                print(f'\rSTATUS: {self.response.json()["status"]}', end="")

                if self.response.json()["status"] == "complete":
                    return self.response.json()
            except:
                pass
            time.sleep(1)

    def get_with_webproxy(self, url):
        data = {
            "server-option": "us13",
            "d": url,
            "allowCookies": "on"
        }
        self.headers["Origin"] = f"{URL_WEB_PROXY}"
        self.headers["Referer"] = f"{URL_WEB_PROXY}/"
        return self.send_request("POST",
                                 f"{URL_WEB_PROXY}/includes/process.php?action=update",
                                 data=data,
                                 headers=self.headers)

    def get_last_doubles(self, web_proxy=False):
        if not web_proxy:
            self.response = self.send_request("GET",
                                              f"{URL_API}/api/roulette_games/recent",
                                              proxies=self.proxies,
                                              headers=self.headers)
        else:
            self.response = self.get_with_webproxy(f"{URL_API}/api/roulette_games/recent")

        if self.response:
            result = {
                "items": [
                    {"color": "branco" if i["color"] == 0 else "vermelho" if i["color"] == 1 else "preto",
                     "value": i["roll"], "created_date": datetime.strptime(
                        i["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
                     } for i in self.response.json()]}
            return result
        return False

    def get_last_crashs(self, web_proxy=False):
        if not web_proxy:
            self.response = self.send_request("GET",
                                              f"{URL_API}/api/crash_games/recent",
                                              proxies=self.proxies,
                                              headers=self.headers)
        else:
            self.response = self.get_with_webproxy(f"{URL_API}/api/crash_games/recent")

        if self.response:
            result = {
                "items": [{"color": "preto" if float(i["crash_point"]) < 2 else "verde", "value": i["crash_point"]}
                          for i in self.response.json()]}
            return result
        return False

    def get_roulettes(self, web_proxy=False):
        if not web_proxy:
            self.response = self.send_request("GET",
                                              f"{URL_API}/api/roulette_games/current",
                                              proxies=self.proxies,
                                              headers=self.headers)
        else:
            self.response = self.get_with_webproxy(f"{URL_API}/api/roulette_games/current")

        return self.response
