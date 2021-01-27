import requests
import json
import asyncio
from datetime import datetime as dt, timedelta
from queue import Queue
import logging
# from APIs.coingecko import CoinGecko
import requests
try:
    from APIs.coingecko import CoinGecko
    from APIs.utils import get_circles
except ModuleNotFoundError:
    from coingecko import CoinGecko
    from utils import get_circles
import collections
from models.global_enums import MessageTypes, Job, Synchronizer, Signal, Threads


class HooAPI:
    def __init__(self, queue: Queue, sync, signals_queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.signals_queue = signals_queue
        self.host = "https://api.hoolgd.com"
        self.session = requests.Session()
        self.symbol = 'GTH-USDT'
        self.loginfo = logging.getLogger(' Hoo ').warning
        self.queue = queue
        self.sync = sync
        self.exchange_name = 'Hoo.com'
        self.coingecko = CoinGecko()
        self.trade_check_time = 2
        self.loop = asyncio.new_event_loop()
        self.counted_trades = collections.deque(maxlen=1000)

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        await self.cache_trades()
        while True:
            while not self.sync.can_fetch_data:
                await asyncio.sleep(0.2)
            # The target time when the data will be calculated and sent
            target_time = dt.utcnow() + timedelta(minutes=5)
            total_sell_amount = 0
            total_buy_amount = 0
            total_buy_price = 0
            total_Sell_price = 0
            total_buy_number = 0
            total_sell_number = 0
            self.loginfo(
                '[+] Checking for new data from hoo.com ...'
            )
            async for new_trades in self.get_new_trades():
                for trade in new_trades:
                    order_type = trade['side']
                    if order_type == 1:
                        # The GTH is bought for USDT
                        total_buy_amount += float(trade['amount'])
                        total_buy_price += float(trade['price'])
                        total_buy_number += 1
                    elif order_type == -1:
                        total_sell_amount += float(trade['amount'])
                        total_Sell_price += float(trade['price'])
                        total_sell_number += 1
                if dt.utcnow() < target_time:
                    await asyncio.sleep(self.trade_check_time)
                    continue
                break
            liquidity = total_buy_amount - total_sell_amount
            if total_buy_price == 0:
                average_buy_price = "There were no Buy Orders in the last 5 minutes"
            else:
                average_buy_price = total_buy_price / total_buy_number
            if total_Sell_price == 0:
                average_Sell_price = "There were no Sell Orders in the last 5 minutes!"
            else:
                average_Sell_price = total_Sell_price / total_sell_number
            data = await self.coingecko.get_data()
            current_price = data['current_price']
            circles = get_circles(liquidity)
            liq_msg = f'Liquidity added/removed : {liquidity} GTH\n{circles}'
            timestamp = dt.utcnow().strftime("%H:%M")
            message = f'**Exchange : ** {self.exchange_name}\n\n**{liq_msg}**\n\n**Current Price :** {current_price}\n\n**Average Buy Price :** {average_buy_price}\
\n\n**Total Number Buy Transactions :** {total_buy_number}\n\n**Average Sell Price :** {average_Sell_price}\n\n**Total Number Sell Transactions :** {total_sell_number}\n\n**Timestamp :** {timestamp}'
            job = Job()
            job.message_type = MessageTypes.TEXT_MESSAGE
            job.message = message
            signal = Signal(Threads.HOO)
            signal.is_data_ready = True
            self.signals_queue.put(signal)
            while not self.sync.all_data_ready:
                await asyncio.sleep(0.1)
            self.queue.put(job)
            signal = Signal(Threads.HOO)
            signal.is_data_sent = True
            signal.is_data_ready = True
            self.signals_queue.put(signal)
            self.loginfo('[+] Hoo API data added to the queue!')

    async def cache_trades(self):
        endpoint = f'{self.host}/open/v1/trade/market?symbol={self.symbol}'
        data = self.session.get(endpoint).json()
        if data['code'] == 0:
            self.counted_trades.extend(data['data'])

    async def get_new_trades(self):
        endpoint = f'{self.host}/open/v1/trade/market?symbol={self.symbol}'
        while True:
            trades = []
            try:
                data = self.session.get(endpoint).json()
            except requests.exceptions.ConnectionError:
                await asyncio.sleep(1)
                continue
            if data['code'] == 0:
                for trade in data['data']:
                    if trade not in self.counted_trades:
                        self.counted_trades.append(trade)
                        trades.append(trade)
            yield trades


if __name__ == "__main__":
    q = Queue()
    s = Synchronizer()
    api = HooAPI(q, s, q)
    api.start()
