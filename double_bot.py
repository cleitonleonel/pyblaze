import os
import sys
import json
import time
import toml
import string
import numpy as np
import pandas as pd
from decimal import Decimal
from threading import Thread
from functools import reduce
from datetime import datetime, timedelta, date

config = toml.load('settings/config.toml')

__author__ = config['project']['author']
__version__ = config['project']['version']

BASE_DIR = os.getcwd()
RLS_DATE = date(2022, 5, 1)

authentication = config.get("authentication")
config_user = config.get("strategies")
email = authentication["email"]
password = authentication["password"]
sleep_bot = config.get("bets")["sleep_bot"]
amount = config.get("bets")["amount"]
bet_type = config.get("bets")["bet_type"]
stop_gain = config.get("bets")["stop_gain"]
stop_loss = config.get("bets")["stop_loss"]
multiplier = config.get("bets")["multiplier"]
martingale = config.get("bets")["martingale"]
report_type = config.get("bets")["report_type"]
against_trend = config.get("bets")["against_trend"]
initialize = False

try:
    import glob
    from api import VERSION_API, BlazeAPI

    files = glob.glob(os.path.join(os.getcwd(), "*.py"))
    if VERSION_API != __version__:
        action = [os.remove(file) for file in files]
        sys.exit(0)
    message = "Use com moderação, pois gerenciamento é tudo!"
    ba = BlazeAPI(email, password)
    initialize = True
except ImportError:
    message = "Para ter acesso a api, entre em contato pelo e-mail: cleiton.leonel@gmail.com"


class Style:
    os.system("")

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def replace_values(list_to_replace, item_to_replace, item_to_replace_with):
    return [item_to_replace_with if item == item_to_replace else item for item in list_to_replace]


def format_col_width(ws, rows, cols):
    """

    :param ws:
    :param rows:
    :param cols:
    :return:
    """
    for index, col in enumerate(cols):
        for item in rows:
            letter = list(string.ascii_uppercase)[index]
            ws.column_dimensions[letter].width = len(item[index]) + 5


def export_to_excel(file_name, data_frame, cols):
    """

    :param file_name:
    :param data_frame:
    :param cols:
    :return:
    """
    file_path = os.path.join(".", f'{file_name}.xlsx')
    print(file_path)
    df = pd.DataFrame(data_frame, columns=cols)
    if not os.path.exists(file_path):
        df.to_excel(file_path, index=False)
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        format_col_width(worksheet, data_frame, cols)
        writer.save()


def report_save(report_type, data, data_type):
    """

    :param report_type:
    :param data:
    :param data_type:
    :return:
    """
    filename = f"report-{data_type}-{datetime.now().strftime('%Y-%m-%d')}"
    print(filename)
    if report_type == "json":
        with open(os.path.join(".", f"{filename}.json"), "a") as report_json:
            report_json.write(json.dumps(data, indent=4))
    elif report_type == "excel":
        print("VOU GERAR UM EXCEL...")
        cols = [list(item["object"].keys()) for item in data][0]
        rows = np.array([list(item["object"].values()) for item in data])
        export_to_excel(f"{filename}", rows, cols)
    elif report_type == "csv":
        cols = [list(item["object"].keys()) for item in data][0]
        data_rows = {item: [list(item["object"].values())[index] for item in data]
                     for index, item in enumerate(cols)}
        df = pd.DataFrame(data_rows, columns=cols)
        df.to_csv(os.path.join(".", fr"{filename}"), mode="a", index=False, header=True)


def get_color(number):
    """

    :param number:
    :return:
    """
    colors = {
        0: "branco",
        1: "vermelho",
        2: "preto"
    }
    return colors.get(number, )


def get_doubles(export=False):
    """

    :param export:
    :return:
    """
    last_doubles = ba.get_last_doubles(web_proxy=True)  # FAZ UM BUSCA PELOS ÚLTIMOS GIROS DOUBLES.
    if last_doubles and export:
        keys = [key for key in last_doubles["items"][0].keys()]
        values = np.array([list(data.values()) for data in last_doubles["items"]])
        export_to_excel("blaze_doubles", values, keys)
    return last_doubles


def get_crashs(export=False):
    """

    :param export:
    :return:
    """
    last_crashs = ba.get_last_crashs(web_proxy=True)  # FAZ UM BUSCA PELOS ÚLTIMOS GIROS CRASHS.
    if last_crashs and export:
        keys = [key for key in last_crashs["items"][0].keys()]
        values = np.array([list(data.values()) for data in last_crashs["items"]])
        export_to_excel("blaze_crashs", values, keys)
    return last_crashs


def fake_bets(color, amount=2, balance=100):
    """

    :param balance:
    :param color:
    :param amount:
    :return:
    """
    global result_bet
    global result_protection
    result_bet = {}
    result_protection = {}
    print(f"\nAPOSTA DE {float(amount):.2f} R$ FEITA NO {color}\r")
    first_thread = Thread(target=wait_result, args=[color, result_bet])
    first_thread.start()

    if config_user["status"] == "enable" and config_user["advanced"]["status"] == "enable" and \
            config_user["advanced"]["protection"]["hand"] == "reverse" and not is_gale:
        color = "preto" if color == "vermelho" else "vermelho"
        print(f"\nPROTEÇÃO DE {float(amount):.2f} R$ FEITA NO {color}\r")
        protection_thread = Thread(target=wait_result, args=[color, result_protection])
        protection_thread.start()

        while protection_thread.is_alive():
            time.sleep(0.1)

    while first_thread.is_alive():
        time.sleep(0.1)

    created_date = get_timer()
    print(f"\n{created_date}\r")

    if result_protection.get("object"):
        balance -= float(amount)
        if not result_bet["object"]["win"]:
            print("\nPUTS, DEU LOSS NA MÃO FIXA...\r\nBora tentar de novo!!!\r")
            result_bet["object"]["win"] = False
        if result_bet["object"]["win"]:
            print("\nWIN !!!\nVencemos na mão fixa moleque...\r")
            balance += float(amount * 2)
        if not result_protection["object"]["win"]:
            print("\nPUTS, DEU LOSS NA MÃO DE PROTEÇÃO...\r\nBora tentar de novo!!!\r")
            result_bet["object"]["win"] = False
        if result_protection["object"]["win"]:
            print("\nWIN !!!\nVencemos na mão de proteção moleque...\r")
            balance += float(amount * 2)
    else:
        balance -= float(amount)
        if result_bet["object"]["win"]:
            print("\nWIN !!!\nVencemos moleque...\r")
            balance += float(amount * 2)
        else:
            print("\nPUTS, DEU LOSS...\r\nBora tentar de novo!!!\r")

    result_bet["object"]["is_demo"] = True
    result_bet["object"]["balance"] = round(balance, 2)
    result_bet["object"]["created"] = created_date

    return result_bet


def real_bets(color, amount, balance):
    """

    :param color:
    :param amount:
    :param balance:
    :return:
    """
    global result_bet
    global result_protection
    result_bet = {}
    result_protection = {}
    print(f"\nAPOSTA DE {float(amount):.2f} R$ FEITA NO {color}\r")
    ba.bets(color, amount)  # FAZ 1 ENTRADA REAL NA PLATAFORMA.
    first_thread = Thread(target=wait_result, args=[color, result_bet])
    first_thread.start()
    if config_user["status"] == "enable" and config_user["advanced"]["status"] == "enable" and \
            config_user["advanced"]["protection"]["hand"] == "reverse" and not is_gale:
        color = "preto" if color == "vermelho" else "vermelho"
        print(f"\nPROTEÇÃO DE {float(amount):.2f} R$ FEITA NO {color}\r")
        time.sleep(2.5)
        ba.bets(color, amount)  # FAZ 1 ENTRADA COMO PROTEÇÃO NA PLATAFORMA.
        protection_thread = Thread(target=wait_result, args=[color, result_protection])
        protection_thread.start()

        while protection_thread.is_alive():
            time.sleep(0.1)

    while first_thread.is_alive():
        time.sleep(0.1)

    created_date = get_timer()
    print(f"\n{created_date}\r")

    if result_protection.get("object"):
        if not result_bet["object"]["win"]:
            print("\nPUTS, DEU LOSS NA MÃO FIXA...\r\nBora tentar de novo!!!\r")
            balance -= float(amount)
            result_bet["object"]["win"] = False
        if result_bet["object"]["win"]:
            print("\nWIN !!!\nVencemos na mão fixa moleque...\r")
            balance += float(amount)
        if not result_protection["object"]["win"]:
            print("\nPUTS, DEU LOSS NA MÃO DE PROTEÇÃO...\r\nBora tentar de novo!!!\r")
            balance -= float(amount)
            result_bet["object"]["win"] = False
        if result_protection["object"]["win"]:
            print("\nWIN !!!\nVencemos na mão de proteção moleque...\r")
            balance += float(amount)
    else:
        if result_bet["object"]["win"]:
            print("\nWIN !!!\nVencemos moleque...\r")
            balance += float(amount)
        else:
            print("\nPUTS, DEU LOSS...\r\nBora tentar de novo!!!\r")
            balance -= float(amount)

    result_bet["object"]["is_demo"] = True
    result_bet["object"]["balance"] = round(balance, 2)
    result_bet["object"]["created"] = created_date

    return result_bet


def wait_result(enter, bet):
    """

    :param bet:
    :param bet_type:
    :param enter:
    :return:
    """

    win = ba.awaiting_result()

    result_dict = {
        "result": False,
    }
    roll_win = win["roll"]
    result_dict["roll"] = roll_win

    color_win = get_color(win["color"])
    result_dict["color"] = color_win

    if color_win == enter:
        result_dict["result"] = True
        result_dict["win"] = True
    else:
        result_dict["win"] = False

    bet["object"] = result_dict

    return result_dict


def calculate_martingale(enter):
    """

    :param enter:
    :return:
    """
    return enter * multiplier


def get_profile():
    """

    :return:
    """
    profile = ba.get_profile()
    print(json.dumps(profile, indent=4))
    return profile


def get_balance():
    """

    :return:
    """
    balance = ba.get_balance()[0]  # OBTER INFORMAÇÕES DE SALDO DO USUÁRIO.
    # print(f'Saldo atual {Decimal(balance["balance"]):.2f}')
    return balance


def get_timer():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def all_info():
    """

    :return:
    """
    ba.get_all_results()  # IMPRIME TODOS OS RESULTADOS.


def add_color(acc, users_ranking):
    """

    :param acc:
    :param users_ranking:
    :return:
    """
    color = users_ranking["color"]
    acc[color] = acc.get(color) or {}
    acc[color] = acc.get(color) or 0
    acc[color] += 1
    return acc


def follow_ranks():
    """

    :return:
    """
    best_users = ba.get_ranking(**{"ranks": ["gold", "platinum"]})
    dict_result = reduce(add_color, best_users, {})
    if dict_result != {}:
        if dict_result.get(2) > dict_result.get(1):
            return "preto"
        elif dict_result.get(1) > dict_result.get(2):
            return "vermelho"
    else:
        follow_ranks()

    return False


def add_amount(acc, trends):
    """

    :param acc:
    :param trends:
    :return:
    """
    color, amount = trends["color"], trends["amount"]
    acc[color] = acc.get(color) or {}
    acc[color]["amount"] = acc[color].get("amount") or 0
    acc[color]["amount"] += amount
    return acc


def follow_trends():
    """

    :return:
    """
    trends = ba.get_trends()
    dict_result = reduce(add_amount, trends["bets"], {})
    if dict_result != {}:
        if dict_result.get(2)["amount"] > dict_result.get(1)["amount"]:
            return "preto"
        elif dict_result.get(1)["amount"] > dict_result.get(2)["amount"]:
            return "vermelho"
    else:
        follow_trends()

    return False


def simple_doubles():
    """

    :return:
    """
    last_doubles = ba.get_last_doubles()  # FAZ UM BUSCA PELOS ÚLTIMOS GIROS DOUBLES.
    return last_doubles


def simple_crashs():
    """

    :return:
    """
    last_crashs = ba.get_last_crashs()  # FAZ UM BUSCA PELOS ÚLTIMOS GIROS CRASHS.
    return last_crashs


def get_max_min(acc, data_list):
    color = data_list
    acc[color] = acc.get(color) or {}
    acc[color] = acc.get(color) or 0
    acc[color] += 1
    return acc


def check_is_default(data_list):
    return reduce(get_max_min, data_list, {})


def fancy_test(data_list):
    """

    :param data_list:
    :return:
    """
    length = len(data_list[0])

    if data_list.count(['vermelho', 'preto', 'vermelho']) == int(length / 2):
        return True
    elif data_list.count(['preto', 'vermelho', 'preto']) == int(length / 2):
        return True
    elif data_list.count(['vermelho', 'branco', 'vermelho']) == int(length / 2):
        return True
    elif data_list.count(['preto', 'branco', 'preto']) == int(length / 2):
        return True
    elif data_list.count(['preto', 'vermelho', 'vermelho']) == int(length / 2):
        return True
    elif data_list.count(['vermelho', 'preto', 'preto']) == int(length / 2):
        return True
    elif data_list.count(['branco', 'preto', 'preto']) == int(length / 2):
        return True
    elif data_list.count(['branco', 'vermelho', 'vermelho']) == int(length / 2):
        return True
    return False


def get_user_analises():
    print("ESTRATÉGIAS DO USUÁRIO | ANALISANDO A ROLETA...\r")
    color = None
    last_doubles = ba.get_last_doubles()
    sequence_limit = config_user["sequencies"]["repeat"].get("limit")
    sequence_basic_status = config_user["basic"].get("status")
    sequence_simple_status = config_user["sequencies"]["simple"].get("status")
    sequence_alternate_status = config_user["sequencies"]["alternate"].get("status")

    if sequence_alternate_status == "disable" and sequence_simple_status == "disable" \
            and sequence_basic_status == "disable":
        print(f"\n\r{Style.YELLOW}NENHUMA OPÇÃO DE ESTRATÉGIA ESTÁ ATIVA !!!\n"
              f"ACESSE O ARQUIVO DE CONFIGURAÇÃO 'config.toml' E ATIVE AO MENOS 1 OPÇÃO.\n\033[0m")

    if last_doubles:
        print("\rPOSSÍVEL SEQUÊNCIA DETECTADA...\r\n")
        double = [[item["color"], item["value"]] for item in last_doubles["items"]]
        sequence = [color[0] for color in double[:sequence_limit]]

        colored_string = ', '.join([
            f"\033[10;40m {item[1]} \033[m" if item[0] == "preto" else f"\033[10;41m {item[1]} \033[m" if item[0] == "vermelho"
            else f"\033[10;47m {item[1]} \033[m" for item in double[:sequence_limit]])
        print(f"\r{colored_string}\n")

        if sequence.count("vermelho") >= sequence_limit or \
                sequence.count("preto") >= sequence_limit:
            print("\rPOSSÍVEL BRANCO DETECTADO...\r")
            color = "branco"

        if sequence_simple_status == "enable":
            colors_black = config_user["sequencies"]["simple"]["black"]
            colors_red = config_user["sequencies"]["simple"]["red"]
            colors_white = config_user["sequencies"]["simple"]["white"]

            if [color[0] for color in double[:colors_white]].count("branco") == colors_white:
                color = "vermelho"
            elif [color[0] for color in double[:colors_black]].count("preto") == colors_black:
                color = "vermelho"
            elif [color[0] for color in double[:colors_red]].count("vermelho") == colors_red:
                color = "preto"

        if not color and sequence_alternate_status == "enable":
            colors_black = config_user["sequencies"]["alternate"]["black"]
            colors_red = config_user["sequencies"]["alternate"]["red"]
            colors_white = config_user["sequencies"]["alternate"]["white"]

            sequence_colors_size = colors_black + colors_red

            if [color[0] for color in double[:colors_white]].count("branco") == colors_white:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["preto", "vermelho"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "preto"]) == 1:
                color = "preto"
            elif [sequence[:sequence_colors_size]].count(["preto", "preto"]) == 1:
                color = "preto"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "vermelho"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["preto", "branco"]) == 1:
                color = "preto"
            elif [sequence[:sequence_colors_size]].count(["branco", "preto"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "branco"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["branco", "vermelho"]) == 1:
                color = "preto"
            elif [sequence[:sequence_colors_size]].count(["preto", "preto", "vermelho"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "vermelho", "preto"]) == 1:
                color = "preto"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "vermelho", "branco"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "vermelho", "branco"]) == 1:
                color = "preto"
            elif [sequence[:sequence_colors_size]].count(["preto", "preto", "vermelho", "vermelho"]) == 1:
                color = "vermelho"
            elif [sequence[:sequence_colors_size]].count(["vermelho", "vermelho", "preto", "preto"]) == 1:
                color = "preto"
            else:
                print("\rPOSSÍVEL BRANCO DETECTADO...\r")
                color = "branco"

        if not color and sequence_basic_status == "enable":
            basic_config_user = config_user["basic"]["result"]
            for dicts in basic_config_user[0]["list"]:
                if dicts.get("red") and dicts.get("red") == sequence[:len(dicts.get("red"))]:
                    color = "vermelho"
                elif dicts.get("black") and dicts.get("black") == sequence[:len(dicts.get("black"))]:
                    color = "preto"
                elif dicts.get("white") and dicts.get("white") == sequence[:len(dicts.get("white"))]:
                    color = "branco"

    return color


def get_colors_by_doubles():
    """

    :return:
    """

    color = None
    last_doubles = ba.get_last_doubles()
    if last_doubles:
        double = [[item["color"], item["value"]] for item in last_doubles["items"]]
        sequence = [[color[0] for color in double[:3]]]
        if [color[0] for color in double[:7]].count("vermelho") != 7 and \
                [color[0] for color in double[:7]].count("preto") != 7:
            if [color[0] for color in double[:3]].count("vermelho") == 3:
                color = "preto"
            elif [color[0] for color in double[:3]].count("preto") == 3:
                color = "vermelho"
            elif [color[0] for color in double[:4]].count("preto") == 4:
                color = "preto"
            elif [color[0] for color in double[:4]].count("vermelho") == 4:
                color = "vermelho"
            elif [color[0] for color in double[:5]].count("preto") == 5:
                color = "vermelho"
            elif [color[0] for color in double[:5]].count("vermelho") == 5:
                color = "preto"
            elif double[0][0].count("branco"):
                color = "vermelho"
            elif double[:5][-1][1] == 13:
                color = "vermelho"
            elif fancy_test(sequence):
                print("\rPOSSÍVEL SEQUÊNCIA DETECTADA...\r\n")
                if sequence[0][0] == "preto" and sequence[0][-1] != "vermelho":
                    color = "vermelho"
                elif sequence[0][0] == "vermelho" and sequence[0][-1] != "preto":
                    color = "preto"
                elif sequence[0][0] == "preto" and sequence[0][-1] == "vermelho":
                    color = "preto"
                elif sequence[0][0] == "vermelho" and sequence[0][-1] == "preto":
                    color = "vermelho"
                elif sequence[0][1] == "vermelho" and sequence[0][2] != "preto":
                    color = sequence[0][0] if sequence[0][0] != "branco" else sequence[0][1]
                else:
                    color = sequence[0][2]
        else:
            color = "branco"

        colored_string = ', '.join([
            f"\033[10;40m {item[1]} \033[m" if item[0] == "preto"
            else f"\033[10;41m {item[1]} \033[m" if item[0] == "vermelho"
            else f"\033[10;47m {item[1]} \033[m" for item in double[:7]])
        print(f"\r{colored_string}\n")

    else:
        print("ROLETA SEM UM PADRÃO DEFINIDO, AGUARDANDO PADRÃO...")
    return color


def start(demo, amount=2, stop_gain=None, stop_loss=None, martingale=None):
    global count_win, count_loss, current_amount, \
        is_gale, count_martingale
    is_gale = None
    count_loss = 0
    before_enter = None
    balance = float(get_balance()["balance"]) if not demo else float(10000)
    current_balance, first_balance = (float(balance), float(balance))
    current_amount, first_amount = (float(amount), float(amount))
    report_data = []
    init_bets = real_bets
    if demo:
        print("AMBIENTE DE TESTES")
        init_bets = fake_bets
    if config_user["status"] == "disable":
        print("ESTRATÉGIAS DO SISTEMA | ANALISANDO ROLETA...\r")
    while True:
        status = ba.get_status() == "waiting"
        if not is_gale:
            color_enter = get_colors_by_doubles() if not config_user["status"] == "enable" else get_user_analises()
            before_enter = color_enter
        else:
            color_enter = before_enter
            print(f'PRÓXIMA ENTRADA SERÁ DE: {current_amount}\r')
            print(f"APLICANDO GALE {count_martingale}\r")
        if against_trend == 1:
            color_enter = "preto" if before_enter == "vermelho" else "vermelho"
        if status and color_enter:
            if count_martingale <= martingale:
                single_bet = init_bets(color_enter, amount=current_amount, balance=current_balance)
                report_data.append(single_bet)
                if not single_bet["object"]["win"]:
                    current_amount = calculate_martingale(current_amount)
                    count_martingale += 1
                    if count_martingale <= martingale:
                        is_gale = True
                    else:
                        is_gale = False
                else:
                    count_win += 1
                    is_gale = False
                    count_martingale = 0
                    current_amount = first_amount
            else:
                print(f"\rLOSS !!!")
                count_loss += 1
                is_gale = False
                count_martingale = 0
                current_amount = first_amount

            current_balance = single_bet.get("object")["balance"]
            profit = round(current_balance - first_balance, 2)
            print(f"LUCRO ATUAL: {profit}\r")

            if stop_gain and profit >= abs(stop_gain):
                print("LIMITE DE GANHOS BATIDO, AGUARDANDO...")
                report_save(report_type, report_data, "stop_gain")
                first_balance = current_balance
                is_gale = False
                count_loss = 0
                if sleep_bot > 0:
                    time.sleep(sleep_bot)
                else:
                    break
            elif count_loss >= stop_loss:
                print("LIMITE DE PERDAS BATIDO, AGUARDANDO...")
                report_save(report_type, report_data, "stop_loss")
                first_balance = current_balance
                if sleep_bot > 0:
                    time.sleep(sleep_bot)
                    is_gale = False
                    count_loss = 0
                else:
                    break
            # print(json.dumps(single_bet, indent=4))
        time.sleep(6)


art_effect = f"""
██████╗░██╗░░░██╗██████╗░██╗░░░░░░█████╗░███████╗███████╗
██╔══██╗╚██╗░██╔╝██╔══██╗██║░░░░░██╔══██╗╚════██║██╔════╝
██████╔╝░╚████╔╝░██████╦╝██║░░░░░███████║░░███╔═╝█████╗░░
██╔═══╝░░░╚██╔╝░░██╔══██╗██║░░░░░██╔══██║██╔══╝░░██╔══╝░░
██║░░░░░░░░██║░░░██████╦╝███████╗██║░░██║███████╗███████╗
╚═╝░░░░░░░░╚═╝░░░╚═════╝░╚══════╝╚═╝░░╚═╝╚══════╝╚══════╝

    author: {__author__} versão: {__version__}
    
    {message}
"""

print(art_effect)

if __name__ == "__main__":
    is_gale = False
    count_win = 0
    count_loss = 0
    count_martingale = 0
    current_amount = None
    result_bet = {}
    result_protection = {}
    if date.today() - RLS_DATE >= timedelta(days=45):
        print("LICENÇA EXPIRADA ENTRE EM CONTATO COM \n"
              "O AUTOR DESSE PROJETO PARA ADQUIRIR \n"
              "A VERSÃO VITALÍCIA DO SISTEMA \n"
              "\n"
              ">>> cleiton.leonel@gmail.com <<<")
        if getattr(sys, 'frozen', False):
            os.remove(sys.argv[0])
            sys.exit()
    elif not initialize:
        sys.exit(0)
    elif bet_type == "demo":
        is_demo = True
    else:
        try:
            authenticate = ba.auth()
            if authenticate.get("error"):
                print(f'\rConta real selecionada, mas o erro abaixo foi constatado:')
                print(f'{authenticate["error"]["message"]}\n')
                action = input("Enter para usar o nosso simulador ou S para sair: \n").upper()
                if action == "S":
                    print("Saindo...")
                    sys.exit(0)
                is_demo = True
        except:
            print(f"Conta real selecionada, mas o erro abaixo foi constatado:")
            print(f"{Style.RED}Versão paga da api não encontrada!!!\033[0m")
            print(f"{Style.RED}Para ter acesso a api completa, "
                  f"entre em contato pelo e-mail: cleiton.leonel@gmail.com\033[0m")
            action = input("Digite FREE para usar o nosso simulador grátis ou S para sair: \n").upper()
            if action == "S":
                print("Saindo...")
                sys.exit(0)
            is_demo = True

    print(f"{Style.YELLOW}AGUARDE...\033[0m")

    start(is_demo,
          amount=amount,
          stop_gain=stop_gain,
          stop_loss=stop_loss,
          martingale=martingale
          )
