
import logging
import json
from telethon import TelegramClient
from queue import Queue
import asyncio
from collections import deque
from models.global_enums import MessageTypes, Job


class Reposter:
    def __init__(self, message_queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.message_queue = message_queue
        self.loginfo = logging.getLogger(' Reposter ').info
        self.logerror = logging.getLogger(' Reposter ').error
        self.loop = asyncio.new_event_loop()
        self.itter_time = 2700

    def start(self):
        self.loginfo('[+] Starting Reposter ...')
        self.loop.run_until_complete(self.main())

    async def main(self):
        self.loginfo('[+] Re-Poster is ready!')
        while True:
            await asyncio.sleep(self.itter_time)
            job = Job()
            job.message_type = MessageTypes.REPOST
            self.message_queue.put(job)
