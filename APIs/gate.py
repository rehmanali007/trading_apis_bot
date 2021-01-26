import asyncio
import logging
import requests
from pprint import pprint
from queue import Queue
from datetime import datetime as dt, timedelta
try:
    from APIs.utils import get_circles
    from APIs.coingecko import CoinGecko
except ModuleNotFoundError:
    from utils import get_circles
    from coingecko import CoinGecko
# from APIs.coingecko import CoinGecko
from emoji import emojize
import collections
from models.global_enums import MessageTypes, Job


class Gate:
    def __init__(self, queue):
        self.queue = queue
        self.gth_usdt = "https://data.gateapi.io/api2/1/tradeHistory/gth_usdt"
        self.gth_eth = "https://data.gateapi.io/api2/1/tradeHistory/gth_eth"
        self.loop = asyncio.new_event_loop()
        self.session = requests.Session()
        self.trades_check_time = 10
        self.exchange_name = 'Gate.io'
        self.coingecko = CoinGecko()
        self.loginfo = logging.getLogger(' Gate ').info
        self.counted_trades = collections.deque(maxlen=1000)

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        await self.cache_usdt_trades()
        while True:
            target_time = dt.utcnow() + timedelta(minutes=5)
            total_sell_amount = 0
            total_buy_amount = 0
            total_sell_price = 0
            total_sell_number = 0
            total_buy_price = 0
            total_buy_number = 0
            self.loginfo('[+] Checking for new data from gate.io ..')
            # new_usdt_trades = await self.get_new_usdt_trades()
            async for new_usdt_trades in self.get_new_usdt_trades():
                for trade in new_usdt_trades:
                    if trade['type'] == 'sell':
                        total_sell_amount += float(trade['amount'])
                        total_sell_price += float(trade['rate'])
                        total_sell_number += 1
                    elif trade['type'] == 'buy':
                        total_buy_amount += float(trade["amount"])
                        total_buy_price += float(trade['rate'])
                        total_buy_number += 1
                if dt.utcnow() < target_time:
                    await asyncio.sleep(self.trades_check_time)
                    continue
                break
            liquidity = total_buy_amount - total_sell_amount
            if total_sell_price == 0:
                average_Sell_price = "There were no Sell Orders in the last 5 minutes!"
            else:
                average_Sell_price = total_sell_price / total_sell_number
            if total_buy_price == 0:
                average_buy_price = "There were not Buy Orders in the last 5 minutes!"
            else:
                average_buy_price = total_buy_price / total_buy_number
            data = await self.coingecko.get_data()
            current_price = data['current_price']
            circles = get_circles(liquidity)
            liq_msg = f'Liquidity added/removed : {liquidity} GTH\n{circles}'
            timestamp = dt.utcnow().strftime("%H:%M")
            message = f'**Exchange : ** {self.exchange_name}\n\n**{liq_msg}**\n\n**Current Price :** {current_price}\n\n**Average Buy Price :** {average_buy_price}\
\n\n**Total Number of Buy Trades :** {total_buy_number}\n\n**Average Sell Price :** {average_Sell_price}\n\n**Total Number of Sell Trades :** {total_sell_number}\n\n**Timestamp :** {timestamp}'
            job = Job()
            job.message_type = MessageTypes.TEXT_MESSAGE
            job.message = message
            self.queue.put(job)
            self.loginfo('[+] Gate API data added to the queue!')

    async def create_messages_for_usdt(self, trades):
        messages = list()
        for trade in trades:
            usd_value = trade['total']
            gth_value = trade['amount']
            time = dt.utcfromtimestamp(int(trade['timestamp']))
            if trade['type'] == 'buy':
                # Bought ETH / Sold GTH
                message = f'**Sold {gth_value} GTH for {usd_value} USD on Gate.io**\
\n**Timestamp :** {time} (UTC)'
            if trade['type'] == 'sell':
                # Sold ETH / Bought GTH
                message = f'**Bought {gth_value} GTH for {usd_value} ETH on Gate.io**\
\n**Timestamp :** {time} (UTC)'

            messages.append(message)
        return messages

    async def cache_usdt_trades(self):
        data = self.session.get(self.gth_usdt).json()
        if data['result']:
            self.counted_trades.extend(data['data'])

    async def get_new_usdt_trades(self):
        while True:
            trades = []
            try:
                data = self.session.get(self.gth_usdt).json()
            except requests.exceptions.ConnectionError:
                await asyncio.sleep(1)
                continue
            if not data['result']:
                yield trades
            for trade in data['data']:
                if trade not in self.counted_trades:
                    self.counted_trades.append(trade)
                    trades.append(trade)
            yield trades


if __name__ == "__main__":
    q = Queue()
    g = Gate(q)
    g.start()
