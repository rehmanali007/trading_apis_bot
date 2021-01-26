from python_graphql_client import GraphqlClient
import asyncio
import logging
from datetime import datetime as dt, timedelta
try:
    from APIs.coingecko import CoinGecko
    from APIs.utils import get_circles
except ModuleNotFoundError:
    from utils import get_circles
    from coingecko import CoinGecko
from emoji import emojize
import collections
from models.global_enums import MessageTypes, Job
import requests


class UniSwap:
    def __init__(self, queue):
        self.queue = queue
        # pg_endpoint = 'https://thegraph.com/explorer/subgraph/uniswap/uniswap-v2'
        endpoint = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'
        self.client = GraphqlClient(
            endpoint=endpoint)
        self.loop = asyncio.new_event_loop()
        self.itter_time = 30
        self.loginfo = logging.getLogger(' UniSwap ').warning
        self.coingecko = CoinGecko()
        self.exchange_name = 'Uniswap.com'
        self.gth_pair_id = '0xb38be7fd90669abcdfb314dbddf6143aa88d3110'
        self.last_trade_timestamp = dt.utcnow() - timedelta(minutes=5)
        self.swaps_check_time = 10
        self.counted_swaps = collections.deque(maxlen=1000)

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        self.loginfo('[+] UniSwap Thread is ready!')
        await self.cache_swaps()
        while True:
            target_time = dt.utcnow() + timedelta(minutes=5)
            # Total_sell_amount will store the total sell values of the orders found in each loop
            total_sell_amount = float(0)
            # Total_buy_amount will store the total buy values of the orders found in each loop
            total_buy_amount = float(0)
            # Total_Sell_Number will store the total number of sells in each loop
            total_sell_transactions = int(0)
            total_sell_price = int(0)
            total_Buy_transactions = int(0)
            total_sell_price = float(0)
            total_buy_price = float(0)
            self.loginfo('[+] Checking for new data from uniswap ..')
            # In the below loop we are gonna store the amounts of all the buy and sell
            # order separatley in total_sell_amount and total_buy_amount.
            async for swaps in self.get_swaps():
                # self.loginfo(f'Got {len(swaps)} new swaps')
                for swap in swaps:
                    if swap['amount0In'] == "0":
                        # ETH is bought and GTH is Sold.
                        gth_value = swap['amount1In']
                        gth_sell_price = swap['amountUSD']
                        total_sell_amount += float(gth_value)
                        total_sell_price += float(gth_sell_price)
                        total_sell_transactions += 1
                    elif swap['amount0Out'] == "0":
                        # It means that ETH is sold and GTH is bought.
                        gth_value = swap["amount1Out"]
                        gth_buy_price = swap['amountUSD']
                        total_buy_amount += float(gth_value)
                        total_buy_price += float(gth_buy_price)
                        total_Buy_transactions += 1
                if dt.utcnow() < target_time:
                    await asyncio.sleep(self.swaps_check_time)
                    continue
                # Synchronize the app time with utc time and go back 6 minutes.
                break
            # Here calculating the liquidity.
            liquidity = total_buy_amount - total_sell_amount
            # self.loginfo(f'Uniswap liquidity : {liquidity}')
            # Here we are getting the coingecko data from coingecko API.
            data = await self.coingecko.get_data()
            current_price = data['current_price']
            if total_sell_amount == 0:
                average_sell_price = "There were no Sell Orders in the last 5 mins"
            else:
                average_sell_price = total_sell_price / total_sell_amount
            if total_buy_amount == 0:
                average_buy_price = "There were no Buy Orders in the last 5 mins"
            else:
                average_buy_price = total_buy_price / total_buy_amount
            circles = get_circles(liquidity)
            liq_msg = f'Liquidity added/removed : {liquidity} GTH\n{circles}'
            self.last_trade_timestamp = dt.utcnow() - timedelta(minutes=5)
            timestamp = dt.utcnow().strftime("%H:%M")
            message = f'Exchange : {self.exchange_name}\n\n**{liq_msg}**\n\n**Current Price :** {current_price}\n\n**Average Buy Price:** {average_buy_price}\
\n\n**Number of Buy Transactions :** {total_Buy_transactions}\n\n**Average Sell Price :** {average_sell_price}\n\n**Number of Sell Transactions :** {total_sell_transactions}\n\n**Timestamp :** {timestamp}'
            job = Job()
            job.message_type = MessageTypes.TEXT_MESSAGE
            job.message = message
            self.queue.put(job)
            self.loginfo('[+] Uniswap API data added to the queue!')
            # await asyncio.sleep(self.itter_time)

    async def create_messages(self, swaps):
        messages = []
        # eth_price = await self.get_eth_price()
        # totals = await self.get_total_volume()
        for swap in swaps:
            # token0 : ETH
            # token1 : GTH
            # amount0In : amount of token0 sold
            # amount0Out : amount of token0 received
            # amount1In : amount of token1 sold
            # amount1Out : amount of token1 received
            time = dt.utcfromtimestamp(int(swap['timestamp']))
            if swap['amount0In'] == "0":
                # ETH is bought and GTH is Sold.
                gth_value = swap['amount1In']
                eth_value = swap['amount0Out']
                message = f'**Sold {gth_value} GTH for {eth_value} ETH on Uniswap**'
            elif swap['amount0Out'] == "0":
                # It means that ETH is sold and GTH is bought.
                eth_value = swap["amount0In"]
                gth_value = swap["amount1Out"]
                message = f'**Bought {gth_value} GTH for {eth_value} ETH on Uniswap.**\n**Timestamp :** {time} (UTC)'
            messages.append(message)
        return messages

    async def get_eth_price(self):
        query = """
            {
                bundle(id: "1" ) {
                ethPrice
                }
            }
        """
        data = self.client.execute(query)
        if 'data' in data:
            return data['data']['bundle']['ethPrice']
        return await self.get_eth_price()

    async def cache_swaps(self):
        query = '''
            query swapsQuery($pair_id: String, $timestamp: Int){
                swaps(orderBy: timestamp, orderDirection: desc, where: {pair: $pair_id}){
                    timestamp
                    id
                    amount0In
                    amount1In
                    amount0Out
                    amount1Out
                    amountUSD
                    transaction{
                        id
                    }
                }
            }
        '''
        var = {
            "pair_id": self.gth_pair_id
        }
        data = self.client.execute(query, variables=var)
        if 'data' in data:
            self.counted_swaps.extend(data['data']['swaps'])

    async def get_swaps(self):
        query = '''
            query swapsQuery($pair_id: String, $timestamp: Int){
                swaps(orderBy: timestamp, orderDirection: desc, where: {pair: $pair_id}){
                    timestamp
                    id
                    amount0In
                    amount1In
                    amount0Out
                    amount1Out
                    amountUSD
                    transaction{
                        id
                    }
                }
            }
        '''
        var = {
            "pair_id": self.gth_pair_id
        }
        while True:
            self.last_trade_timestamp = self.last_trade_timestamp + \
                timedelta(seconds=10)
            try:
                data = self.client.execute(query, variables=var)
            except requests.exceptions.ConnectionError:
                await asyncio.sleep(1)
                continue
            swaps = []
            if 'data' in data:
                for swap in data['data']['swaps']:
                    if swap not in self.counted_swaps:
                        swaps.append(swap)
                        self.counted_swaps.append(swap)
            yield swaps

    async def get_new_swaps(self):
        # Here we will get the swaps data from API and filter the data for previous 5 minutes.
        self.loginfo('Starting to get new swaps...')
        query = '''
            query swapsQuery($pair_id: String, $timestamp: Int){
                swaps(orderBy: timestamp, orderDirection: desc, where: {pair: $pair_id, timestamp_gt: $timestamp}){
                    timestamp
                    id
                    amount0In
                    amount1In
                    amount0Out
                    amount1Out
                    amountUSD
                }
            }
        '''
        # This is the line you need to change in order to get the data you want.
        # We are subtracting time from current time to go back to time and check which trades have timestamp greater then
        # that timestamp. For example.
        # If current time is 12:50 and we want to check trades after 12:45 we will do " - timedelta(minutes=5) " which
        # will subtract 5 minutes from current time and give us 12:45
        time = dt.utcnow() - timedelta(minutes=5)
        self.loginfo(f'Getting data after : {time}')
        timestamp = time.timestamp()
        var = {
            "pair_id": self.gth_pair_id,
            "timestamp": int(timestamp)
        }
        data = self.client.execute(query, variables=var)

        def filter_swaps(swap):
            # API is not giving us the exact filtered data based on time so we are filtering manually
            swap_time = dt.utcfromtimestamp(int(swap['timestamp']))
            if swap_time > time:
                return True
            return False
        if 'data' in data:
            trades = list(filter(filter_swaps, data['data']['swaps']))
            return trades
        return []

    async def get_total_volume(self):
        query = '''
            {
                    uniswapFactory(id: "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"){
                    totalVolumeUSD
                    totalLiquidityUSD
                }
            }
        '''
        data = self.client.execute(query)
        if 'data' in data:
            return data['data']['uniswapFactory']
        return None


if __name__ == "__main__":
    import queue
    q = queue.Queue()
    uni = UniSwap(q)
    uni.start()
