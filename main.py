from telethon import TelegramClient, events
import json
import logging
import os
import threading
from queue import Queue
from tg.sender import Sender
from twitter.monitor import Monitor
from twitter.twitter_count import WordCounter
from APIs.uniswap import UniSwap
from APIs.gate import Gate
from APIs.hoo import HooAPI
from APIs.bithumbGlobal import BithumbAPI
from models.gather_blog import BlogScraper
from models.hour_post import Hourly_post
from models.etherscan import Etherscan
from tg.reposter import Reposter
from models.graph import FetchGraph
from models.global_enums import Synchronizer
from APIs.sync import ControlThread


if not os.path.exists('./logs'):
    os.mkdir('logs')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formator = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler = logging.FileHandler('logs/app.log')
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(formator)
logger.addHandler(fileHandler)

f = open('config.json', 'r')
config = json.load(f)

# bot = TelegramClient('bot', config.get("TELEGRAM_API_ID"),
#                      config.get("TELEGRAM_API_HASH"))
# bot.parse_mode = 'md'
client = TelegramClient('client', config.get("TELEGRAM_API_ID"),
                        config.get("TELEGRAM_API_HASH"))
# ALl the APIs messages should be gone through this queue
message_queue = Queue()
signals_queue = Queue()

eth = Etherscan()
# To get the holders value use value = next(get_holders)
# Pass get_holders to the all the threads where it is needed.
get_holders = eth.get_holders()

# Start the twitter monitor thread
twitter_monitor = Monitor(message_queue)
threading.Thread(target=twitter_monitor.start).start()

word_counter = WordCounter(message_queue)
threading.Thread(target=word_counter.start).start()


# Start message sender thread to send the messages to channel
sender = Sender(client, message_queue)
threading.Thread(target=sender.start).start()

sync = Synchronizer()
control = ControlThread(signals_queue, sync)
threading.Thread(target=control.start).start()
# Start 4 APIs threads
uniswap = UniSwap(message_queue, sync, signals_queue)
threading.Thread(target=uniswap.start).start()

hoo = HooAPI(message_queue, sync, signals_queue)
threading.Thread(target=hoo.start).start()

gate = Gate(message_queue, sync, signals_queue)
threading.Thread(target=gate.start).start()

bithumb = BithumbAPI(message_queue, sync, signals_queue)
threading.Thread(target=bithumb.start).start()


# Thread to scrape blog posts
scraper = BlogScraper(message_queue)
threading.Thread(target=scraper.start).start()


# Thread to hourly post
hour_post = Hourly_post(message_queue, get_holders)
threading.Thread(target=hour_post.start).start()

# # Thread to get the latest graph every 30 minutes.
graph = FetchGraph(message_queue)
threading.Thread(target=graph.start).start()

reposter = Reposter(message_queue)
threading.Thread(target=reposter.start).start()


@client.on(events.NewMessage(chats=['https://t.me/GatherAnnouncement']))
async def handle(event):
    text = event.message.message
    message = f'**New Announcement**\n\n{text}'
    message_queue.put(message)


# Start the telegram bot as the main thread
# bot.start(bot_token=config.get("TELEGRAM_BOT_TOKEN"))
client.start(phone=config.get("TELEGRAM_PHONE_NUMBER"))
client.parse_mode = 'md'
logger.warning('[+] Client is conntected to telegram!')
client.run_until_disconnected()
