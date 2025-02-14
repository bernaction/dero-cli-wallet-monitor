#!/usr/bin/env python3
'''
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.
'''

import os
import sys
import time
import json
import requests
import argparse
import PySimpleGUI as sg
from dateutil import parser
from playsound import playsound
import pygame
from colorama import init

from collections import deque
from datetime import datetime, timedelta

RATIO = 100000
wallet_rpc_server = "http://127.0.0.1:10103/json_rpc"
node_rpc_server = None
agora = datetime.now()
HEIGHT = 0
DAYS = 7
MINIBLOCK_WORTH = 0.0615
GRAPH_WIDTH = 50
TIME_SLEEP = 30


def get_arguments():
    """
    parse the argument provided to the script
    """
    parser = argparse.ArgumentParser(
        description='DeroHE wallet monitor',
        epilog='Created by 51|Fu.R4nk',
        usage='python3 %s [-a]')
    parser.add_argument('--rpc-server',
                        action='store',
                        help='Wallet rpc-server address. Default 127.0.0.1:10103')
    parser.add_argument('--node-rpc-server',
                        action='store',
                        help='Node wallet rpc-server address.')
    parser.add_argument('--notify-count',
                        action='store',
                        help="Notify if you don't get reward after X minutes. defult disabled")
    parser.add_argument('--one-shot',
                        action='store_true',
                        help="Display data and exit")
    parser.add_argument('--day-range',
                        action='store', type=int,
                        help="Number of days to plot. Default 7")
    return parser.parse_args()


class WalletParser():
    def __init__(self, rpc_server, days=7):
        self.rpc_server = rpc_server
        self.height = self.get_height()
        self.days = int(days)
        from_block = 5000 * self.days  # considering 18 second block is around 4800 block every day
        self.min_height = self.height - from_block if (self.height - from_block) >= 0 else 0
        self.gains = self.populate_history()
        self.daily_gain = self.daily_totals()

    def generic_call(self, method, params=None):
        headers = {'Content-Type': 'application/json'}
        body = {"jsonrpc": "2.0",
                "id": "1",
                "method": method,
                "params": params}
        try:
            r = requests.post(self.rpc_server, json=body,
                              headers=headers, timeout=(9, 120))
        except:
            print("RPC not found. Terminating")
            sys.exit()
        return r

    def get_balance(self):
        result = self.generic_call("GetBalance")
        try:
            return json.loads(result.text)['result']['balance'] / RATIO
        except:
            print("Fail to get balance from RPC. Terminating")
            sys.exit()
        return None

    def get_height(self):
        result = self.generic_call("GetHeight")
        try:
            return json.loads(result.text)['result']['height']
        except:
            print("Fail to get height from RPC. Terminating")
            sys.exit()
        return None

    def get_transfers(self, param=None):
        result = self.generic_call("GetTransfers", param)
        return json.loads(result.text)

    def clean_date(self, date):
        return parser.parse(date, ignoretz=True).replace(second=0, microsecond=0)

    def discretize_history(self, items, start_date):
        amount_by_minute = dict()
        now = datetime.today().replace(second=0, microsecond=0)
        while start_date <= now:
            amount_by_minute[start_date] = 0
            start_date += timedelta(minutes=1)
        max_height = 0
        for item in items:
            short_date = self.clean_date(item['time'])
            if short_date in amount_by_minute.keys():
                amount_by_minute[short_date] += item['amount']
        return amount_by_minute

    def daily_totals(self):
        amount_by_day = dict()
        start_date = (datetime.today() - timedelta(days=self.days)
                      ).replace(hour=0, minute=0, second=0, microsecond=0)

        now = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        while start_date <= now:
            amount_by_day[start_date] = 0
            start_date += timedelta(days=1)
        while len(amount_by_day) > self.days:
            amount_by_day.pop(min(amount_by_day))
        raw_items = self.get_transfers({'coinbase': True, 'min_height': self.min_height})
        if 'entries' in raw_items['result']:
            items = raw_items['result']['entries']
            for item in items:
                short_date = self.clean_date(item['time']).replace(hour=0, minute=0, second=0, microsecond=0)
                if short_date in amount_by_day.keys():
                    amount = item['amount'] / RATIO
                    if amount > 100:
                        continue
                    amount_by_day[short_date] += amount
        return amount_by_day

    def populate_history(self):
        coinbase = self.get_transfers({'coinbase': True, 'min_height': self.min_height})
        last_7D = (datetime.today() - timedelta(days=7)
                   ).replace(second=0, microsecond=0)
        last_24H = datetime.today() - timedelta(days=1)
        last_12H = datetime.today() - timedelta(hours=12)
        last_6H = datetime.today() - timedelta(hours=7)
        last_1H = datetime.today() - timedelta(hours=2)
        last_15M = datetime.today() - timedelta(minutes=15)
        gains = dict()
        gains['avg_15'] = deque(maxlen=15)
        gains['avg_60'] = deque(maxlen=60)
        gains['avg_360'] = deque(maxlen=360)
        gains['avg_720'] = deque(maxlen=720)
        gains['avg_1440'] = deque(maxlen=1440)
        gains['avg_10080'] = deque(maxlen=10080)
        if 'entries' in coinbase['result']:
            short_hist = self.discretize_history(coinbase['result']['entries'], last_7D)
            for item in short_hist:
                amount = short_hist[item] / RATIO
                if amount > 100:
                    continue
                if item > last_7D:
                    gains['avg_10080'].append(amount)
                if item > last_24H:
                    gains['avg_1440'].append(amount)
                if item > last_12H:
                    gains['avg_720'].append(amount)
                if item > last_6H:
                    gains['avg_360'].append(amount)
                if item > last_1H:
                    gains['avg_60'].append(amount)
                if item > last_15M:
                    gains['avg_15'].append(amount)
        return gains

    def update_chart(self, diff):
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        if today == max(self.daily_gain):
            self.daily_gain[today] += diff
        elif today > max(self.daily_gain):
            self.daily_gain.pop(min(self.daily_gain))
            self.daily_gain[today] = diff

    def get_diff(self, height):
        amounts = 0.0
        coinbase = self.get_transfers({'coinbase': True, 'min_height': height})
        if 'entries' in coinbase['result'].keys():
            items = coinbase['result']['entries']
            for item in items:
                if item['height'] <= height:
                    break
                amount = item['amount'] / RATIO
                if amount > 100:
                    continue
                amounts += amount
                hora = agora.strftime("%d/%m/%Y %H:%M:%S")
                print(f"\n\n\nDERO MINI-BLOCK FOUND")
                print("MB:{} in {}\n\n\n".format(item['height'], hora))
                dialog("Dero Mini-Block Found!", item['height'], hora)
                sys.stdout.write('\033c')
                sys.stdout.write("\r")

        return amounts

    def update(self):
        diff = 0.0
        current_height = self.get_height()
        if current_height > self.height:
            diff = self.get_diff(self.height)
            self.height = current_height
        self.update_chart(diff)
        for item in self.gains:
            self.gains[item].append(diff)


class DerodParser:
    def __init__(self, rpc_server):
        self.rpc_server = rpc_server
        self.daily_gain = self.avg_diff()

    def generic_call(self, method, params=None):
        headers = {'Content-Type': 'application/json'}
        body = {"jsonrpc": "2.0",
                "id": "1",
                "method": method,
                "params": params}
        try:
            r = requests.post(self.rpc_server, json=body, headers=headers, timeout=(9, 120))
        except:
            print("RPC not found. Terminating")
            sys.exit()
        return r

    def get_block(self, height):
        result = self.generic_call("DERO.GetBlock", {"height": height})
        return json.loads(result.text)

    def get_info(self):
        result = self.generic_call("DERO.GetInfo")
        return json.loads(result.text)

    def get_height(self):
        data = self.generic_call("DERO.GetHeight")
        return json.loads(data.text)['result']['height']

    def avg_diff(self):
        current_height = self.get_height()
        start_date = (datetime.today() - timedelta(days=7)
                      ).replace(hour=0, minute=0, second=0, microsecond=0)
        diff_by_day = dict()
        now = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        while start_date <= now:
            diff_by_day[start_date] = []
            start_date += timedelta(days=1)
        while len(diff_by_day) > 7:
            diff_by_day.pop(min(diff_by_day))
        for i in range(current_height - 35000, current_height):
            print(i)
            blk = self.get_block(i)
            short_date = datetime.fromtimestamp(blk['result']['block_header']['timestamp'] // 1000).replace(hour=0, minute=0, second=0, microsecond=0)
            if short_date in diff_by_day.keys():
                diff_by_day[short_date].append(int(blk['result']['block_header']['difficulty']))
        for item in diff_by_day:
            if len(diff_by_day[item]) == 0:
                diff_by_day[item] = 0
            else:
                diff_by_day[item] = sum(diff_by_day[item]) / len(diff_by_day[item]) / 1000000000
        return diff_by_day


def plot_graph(daily_gain, unit='DERO'):
    colors = {"blue": "\033[96m",
              "green": "\033[92m",
              "red": "033[93m",
              }
    lines = ""
    bar = ""
    max_value = max(daily_gain.values())
    max_miniblocks = max_value / MINIBLOCK_WORTH

    count = 0
    for item in daily_gain:
        if max_miniblocks > GRAPH_WIDTH:
            percentage = int(daily_gain[item] / max_value * GRAPH_WIDTH)
            bar = "▆" * percentage
        else:
            miniblocks = int(daily_gain[item] / MINIBLOCK_WORTH)
            bar = "■" * miniblocks
        lines += "| {:10}:{:51}{:9.4f} {:4} |\n".format(item.strftime('%Y-%m-%d'), bar, round(daily_gain[item], 4),
                                                        unit)
        count += 1
    return lines


def print_avg(data, supposed_len):
    if supposed_len == 1:
        return "\033[96m{}\033[00m".format(round(sum(data) / supposed_len, 4))
    if len(data) == supposed_len:
        return "\033[92m{}\033[00m".format(round(sum(data) / supposed_len, 4))
    return "\033[93m{}\033[00m".format(round(sum(data) / supposed_len, 4))


def print_sum(data, supposed_len):
    if supposed_len == 1:
        return "\033[96m{:.4f}\033[00m".format(round(sum(data), 4))
    if len(data) == supposed_len:
        return "\033[92m{:.4f}\033[00m".format(round(sum(data), 4))
    return "\033[93m{:.4f}\033[00m".format(round(sum(data), 4))


def compute_power(gain, diff):
    power = dict()
    for item in gain:
        power[item] = (gain[item] / MINIBLOCK_WORTH) * ((diff[item] * 1000000) / 48000) / 1000
    return power


def run(rpc_server, max_zero, node_rpc_server=None, one_shot=False, main_rpc=None):
    count_failure = 0
    passing_time = 0
    flag_notify = True
    diff = 0.0
    wp = WalletParser(rpc_server, DAYS, )
    node_wp = None if node_rpc_server is None else WalletParser(node_rpc_server)
    global fiat, price_change
    try:
        fiat = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=dero').json()[0][
            'current_price']
        price_change = round(requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=dero').json()[0][
            'price_change_percentage_24h'], 2)

    except:
        fiat = 0
        price_change = 0
        print("Coingecko is out")
    dp = None if main_rpc is None else DerodParser(main_rpc)
    while True:
        sys.stdout.write("\r")
        lines = ""
        lines += "--------------------------------------------------------------------------------\n"
        wp.update()
        if node_wp is not None:
            node_wp.update()
        if dp is not None:
            power = compute_power(wp.days, dp.daily_gain)
        lines += "|{:^12}:{:^10}:{:^10}:{:^10}:{:^10}:{:^10}:{:^10}|\n".format(
            'average', '1m', '15m', '1h', '6h', '12h', '24h', '7d')
        lines += "|{:^12}:{:^20}:{:^20}:{:^20}:{:^20}:{:^20}:{:^20}|\n".format('earnings',
                                                                               print_sum([diff], 1),
                                                                               print_sum(wp.gains['avg_15'], 15),
                                                                               print_sum(wp.gains['avg_60'], 60),
                                                                               print_sum(wp.gains['avg_360'], 360),
                                                                               print_sum(wp.gains['avg_720'], 720),
                                                                               print_sum(wp.gains['avg_1440'], 1440),
                                                                               print_sum(wp.gains['avg_10080'], 10080))
        if node_wp is not None:
            lines += "|{:>12}:{:^20}:{:^20}:{:^20}:{:^20}:{:^20}:{:^20}|\n".format('node gain',
                                                                                   print_sum([diff], 1),
                                                                                   print_sum(node_wp.gains['avg_15'],
                                                                                             15),
                                                                                   print_sum(node_wp.gains['avg_60'],
                                                                                             60),
                                                                                   print_sum(node_wp.gains['avg_360'],
                                                                                             360),
                                                                                   print_sum(node_wp.gains['avg_720'],
                                                                                             720),
                                                                                   print_sum(node_wp.gains['avg_1440'],
                                                                                             1440),
                                                                                   print_sum(node_wp.gains['avg_10080'],
                                                                                             10080))
        lines += "|" + " " * 78 + "|\n"
        if diff == 0.0:
            count_failure += 1
        else:
            count_failure = 0
            flag_notify = True
        lines += "| {:14}:{:61} |\n".format("Current height", wp.height)
        lines += "| {:14}:{:61} |\n".format("Wallet amount", wp.get_balance())
        if node_wp is not None:
            lines += "| {:14}:{:61} |\n".format("Node amount", node_wp.get_balance())
        if fiat != 0:
            lines += "| {:14}:{:61} |\n".format("U$ Fiat amount", round(fiat * wp.get_balance(), 3))
        lines += "| {:14}:{:>48} ({:>1}% 24h) |\n".format("U$ Dero", fiat, price_change)
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        lines += "| {:14}:{:>61} |\n".format("Date", formatted_date)
        lines += "----------------------------------- daily sum ----------------------------------\n"
        lines += plot_graph(wp.daily_gain)
        if dp is not None:
            lines += "--------------------------------------------------------------------------------\n"
            lines += "\n"
            lines += plot_graph(dp.daily_gain, "GH/s")
            lines += "--------------------------------------------------------------------------------\n"
            lines += "\n"
            lines += plot_graph(power, "MH/s")
        lines += "--------------------------------------------------------------------------------\n"
        if max_zero > 0:
            if count_failure > max_zero:
                message = 'Since {} minutes you are not receiving rewards!'.format(
                    count_failure)
                lines += "\033[91m{}\033[00m\n".format(message)
                if flag_notify:
                    dialog(message, "", "")
                    count_failure = 0
        if passing_time > 0:
            for item in range(len(lines.split('\n')) - 1):
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
        sys.stdout.write(lines)
        sys.stdout.write(f"refresh in {TIME_SLEEP}s...")
        sys.stdout.flush()
        passing_time += 1
        if one_shot:
            sys.exit(0)
        time.sleep(TIME_SLEEP)


def dialog(message1, message2, message3):
    layout = [
        [sg.Image(filename="dero_logo.png", size=(100, 100), pad=((10, 0), (10, 10)))],
        [sg.Text(message1, size=(30, 1), pad=((10, 0), (0, 10)))],
        [sg.Text(message2, size=(30, 1), pad=((10, 0), (0, 10)))],
        [sg.Text(message3, size=(30, 1), pad=((10, 0), (0, 10)))],
        [sg.Button("OK", size=(10, 1), pad=((10, 10), (0, 10)))]
    ]
    janela = sg.Window("DERO MINI-BLOCK FOUND", layout, size=(400, 400), auto_close=True, auto_close_duration=5)
    # playsound('cash1.mp3')
    pygame.mixer.init()
    pygame.mixer.music.load('coin2.wav')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

    while True:
        evento, valores = janela.read(timeout=10)
        if evento == "OK":
            break
        if evento == sg.WINDOW_CLOSED:
            break
    janela.close()

if __name__ == '__main__':
    max_zero = 0
    args = get_arguments()
    init(autoreset=True)

    # teste caixa de diálogo
    #dialog("Dero Mini-Block Found!", "aaa", agora.strftime("%d/%m/%Y %H:%M:%S"))

    if args.rpc_server:
        wallet_rpc_server = "http://{}/json_rpc".format(args.rpc_server)
    if args.node_rpc_server:
        node_rpc_server = "http://{}/json_rpc".format(args.node_rpc_server)
    if args.notify_count:
        max_zero = int(args.notify_count)
    if args.day_range:
        DAYS = args.day_range
    run(wallet_rpc_server, max_zero, node_rpc_server, args.one_shot)