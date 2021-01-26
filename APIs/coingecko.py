import asyncio
from pprint import pprint
from datetime import datetime as dt
import requests


class CoinGecko:
    def __init__(self):
        self.coin_data_endpoint = 'https://api.coingecko.com/api/v3/coins/gather?localization=false&tickers=true&market_data=true&community_data=false&developer_data=false&sparkline=false'

    async def get_data(self):
        try:
            self.data = requests.get(self.coin_data_endpoint).json()
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
            await asyncio.sleep(1)
            return await self.get_data()
        current_price = self.data['market_data']['current_price']['usd']
        market_cap = self.data['market_data']['market_cap']['usd']
        total_supply = self.data['market_data']['total_supply']
        circulating_supply = self.data['market_data']['circulating_supply']
        data = {
            'current_price': current_price,
            'market_cap': market_cap,
            'total_supply': total_supply,
            'circulating_supply': circulating_supply
        }
        return data


if __name__ == "__main__":
    import queue
    q = queue.Queue()
    cg = CoinGecko()
