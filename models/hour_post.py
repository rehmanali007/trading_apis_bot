import logging
import json
import asyncio
from queue import Queue
import requests
from datetime import datetime as dt
from emoji import emojize
try:
    from APIs.coingecko import CoinGecko
except ImportError:
    from coingecko import CoinGecko
from models.global_enums import MessageTypes, Job


class Hourly_post:
    def __init__(self, queue, get_holders):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.queue = queue
        self.loginfo = logging.getLogger(' Hour Post').warning
        self.logerror = logging.getLogger(' Hour Post ').error
        self.itter_time = 3600
        self.fire = emojize(' :fire: ')
        self.dollar = emojize(':moneybag:', use_aliases=True)
        self.coingecko = CoinGecko()
        self.exchange_name = 'Bithumb.pro'
        self.loop = asyncio.new_event_loop()
        self.get_holders = get_holders

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        while True:
            self.loginfo('[+] Collecting Hourly Data ...')
            data = await self.coingecko.get_data()
            current_price = data['current_price']
            market_cap = data['market_cap']
            circulating_supply = data['circulating_supply']
            total_supply = data['total_supply']
            holders_data = next(self.get_holders)
            timestamp = dt.utcnow().strftime("%H:%M")
            message = f'{self.fire}**Gather Hourly Status Update**{self.fire}\n\n**Current Price :** {self.dollar} {current_price}\
\n\n**Market Cap : **{market_cap}\n\n**Circulating Supply : **{circulating_supply}\n\n**Total Supply : **{total_supply}\n\n**Holders : **{holders_data}\n\n**Timestamp : ** {timestamp}'
            job = Job()
            job.message_type = MessageTypes.TEXT_MESSAGE
            job.message = message
            self.queue.put(job)
            self.bt_data_buy = 0
            self.bt_data_sell = 0
            await asyncio.sleep(self.itter_time)


if __name__ == "__main__":
    q = Queue()
