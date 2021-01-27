import logging
import json
import asyncio
from queue import Queue
import requests
from datetime import datetime as dt, timedelta
from emoji import emojize
try:
    from APIs.coingecko import CoinGecko
    from APIs.utils import get_circles
except ModuleNotFoundError:
    from utils import get_circles
    from coingecko import CoinGecko
import collections
import requests
from models.global_enums import MessageTypes, Job, Synchronizer, Signal, Threads


class BithumbAPI:
    def __init__(self, queue, sync, signals_queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.queue = queue
        self.sync = sync
        self.signals_queue = signals_queue
        self.session = requests.Session()
        self.loginfo = logging.getLogger(' Bithumb API ').warning
        self.logerror = logging.getLogger(' Bithumb API ').error
        self.baseURL = 'https://global-openapi.bithumb.pro/openapi/v1'
        self.target_symbol = 'GTH-USDT'
        self.coingecko = CoinGecko()
        self.exchange_name = 'Bithumb.pro'
        self.loop = asyncio.new_event_loop()
        self.counted_trades = collections.deque(maxlen=1000)
        self.trades_check_time = 10

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        await self.cache_trades()
        while True:
            while not self.sync.can_fetch_data:
                await asyncio.sleep(0.2)
            target_time = dt.utcnow() + timedelta(minutes=5)
            total_buy = 0
            total_sell = 0
            total_buy_prices = float(0)
            total_sell_prices = float(0)
            total_buy_number = float(0)
            total_sell_number = float(0)
            self.loginfo('[+] Checking for new data from bithumb.com ...')
            async for new_trades in self.get_new_trades():
                for trade in new_trades:
                    gth_qty = trade['v']
                    if trade['s'] == 'buy':
                        # Bought GTH
                        total_buy += float(gth_qty)
                        total_buy_prices += float(trade['p'])
                        total_buy_number += 1
                    elif trade['s'] == 'sell':
                        total_sell += float(gth_qty)
                        total_sell_prices += float(trade['p'])
                        total_sell_number += 1
                if dt.utcnow() < target_time:
                    await asyncio.sleep(self.trades_check_time)
                    continue
                break
            liquidity = total_buy - total_sell
            data = await self.coingecko.get_data()
            current_price = data['current_price']
            if total_sell_prices == 0:
                average_Sell_price = "There were no Sell Orders in the last 5 minutes!"
            else:
                average_Sell_price = total_sell_prices / total_sell_number
            if total_buy_prices == 0:
                average_Buy_price = "There were no Buy Orders in the last 5 minutes!"
            else:
                average_Buy_price = total_buy_prices / total_buy_number
            circles = get_circles(liquidity)
            liq_msg = f'Liquidity added/removed : {liquidity} GTH\n{circles}'
            timestamp = dt.utcnow().strftime("%H:%M")
            message = f'**Exchange : ** {self.exchange_name}\n\n**{liq_msg}**\n\n**Current Price :** {current_price}\n\n**Average Buy Price :** {average_Buy_price}\
\n\n**Total Number of Buy Transactions :** {total_buy_number}\n\n**Average Sell Price :** {average_Sell_price}\n\n**Total Number of Sell Transactions :** {total_sell_number}\n\n**Timestamp :** {timestamp}'
            job = Job()
            job.message_type = MessageTypes.TEXT_MESSAGE
            job.message = message
            signal = Signal(Threads.BITHUMB)
            signal.is_data_ready = True
            self.signals_queue.put(signal)
            while not self.sync.all_data_ready:
                await asyncio.sleep(0.1)
            self.queue.put(job)
            signal = Signal(Threads.BITHUMB)
            signal.is_data_sent = True
            signal.is_data_ready = True
            self.signals_queue.put(signal)

    async def create_messages(self, trades):
        messages = []
        for trade in trades:
            '''
            p	deal price
            s	trade type buy or sell	
            v	deal quantity		
            t	timestamp
            '''
            price = trade['p']
            gth_qty = trade['v']
            time = dt.utcfromtimestamp(int(trade['t']))
            if trade['s'] == 'buy':
                # Bought GTH
                message = f'**Bought {gth_qty} GTH for {price} USD on bithumb.pro**\n**Timestamp :** {time} (UTC)'
            if trade['s'] == 'sell':
                # Sold GTH
                message = f'**Sold {gth_qty} GTH for {price} USD on bithumb.pro**\n**Timestamp :** {time} (UTC)'
            messages.append(message)
        return messages

    async def cache_trades(self):
        endpoint = f'{self.baseURL}/spot/trades?symbol={self.target_symbol}'
        data = self.session.get(endpoint).json()
        if 'data' in data:
            self.counted_trades.extend(data['data'])

    async def get_new_trades(self):
        endpoint = f'{self.baseURL}/spot/trades?symbol={self.target_symbol}'
        while True:
            trades = []
            data = self.session.get(endpoint).json()
            for trade in data['data']:
                if trade not in self.counted_trades:
                    self.counted_trades.append(trade)
                    trades.append(trade)
            yield trades


if __name__ == "__main__":
    q = Queue()
    s = Synchronizer()
    api = BithumbAPI(q, s, q)
    api.start()
