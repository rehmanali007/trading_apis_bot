import logging
import json
from telethon import TelegramClient
from queue import Queue
import asyncio


class Sender:
    def __init__(self, client: TelegramClient, queue: Queue, latest_post_queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.client = client
        self.message_queue = queue
        self.latest_post_queue = latest_post_queue
        self.loginfo = logging.getLogger(' Sender ').info
        self.logerror = logging.getLogger(' Sender ').error
        self.thread_ready = False

    def start(self):
        self.loginfo('[+] Starting Message Pin and Sender ...')
        self.client.loop.create_task(self.main())

    async def main(self):
        while not self.client.is_connected():
            self.loginfo('[*] Pinner is waiting for client to connect!')
            await asyncio.sleep(1)
        while not self.thread_ready:
            self.loginfo('[+] Setting up pin and send')
            dialogs = await self.client.get_dialogs()
            target_channel = None
            for d in dialogs:
                if d.title == self.config.get("DEST_TG_CHANNEL_NAME"):
                    self.loginfo(
                        '[+] Destination channel found for Pin and Sender!')
                    target_channel = d
                    self.thread_ready = True
                    break
            if target_channel is None:
                self.logerror('[-] Destination channel not found!')
                exit()
        self.loginfo('[+] Message send and pin is ready!')
        while True:
            message = self.message_queue.get()
            sent_message = await self.client.send_message(target_channel, message)
            await self.client.pin_message(target_channel, sent_message)
            self.latest_post_queue.append(sent_message)
            self.message_queue.task_done()
