import logging
import os
import json
from telethon import TelegramClient
from tg.fast_streams import upload_file
from queue import Queue
import asyncio
from io import BytesIO


class Sender:
    def __init__(self, client: TelegramClient, queue: Queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.client = client
        self.queue = queue
        self.loginfo = logging.getLogger(' Sender ').info
        self.logerror = logging.getLogger(' Sender ').error

    def start(self):
        self.loginfo('[+] Starting Graph sender ...')
        self.client.loop.create_task(self.main())

    async def main(self):
        while not self.client.is_connected():
            self.loginfo('[*] Graph sender waiting for client to connect!')
            await asyncio.sleep(1)
        dialogs = await self.client.get_dialogs()
        target_channel = None
        for d in dialogs:
            if d.title == self.config.get("DEST_TG_CHANNEL_NAME"):
                self.loginfo('[+] Destination channel found for Graph!')
                target_channel = d
                break
        if target_channel is None:
            self.loginfo('[-] Destination channel not found!')
            exit()
        self.loginfo('[+] Graph sender is ready!')
        while True:
            location = self.queue.get()
            self.loginfo('[+] Uploading the graph to channel ..')
            with open(location, 'rb') as fh:
                buf = BytesIO(fh.read())
            uploaded_file = await upload_file(self.client, buf)
            await self.client.send_message(target_channel, file=uploaded_file)
            print('Graph sent to target channel!')
            os.remove(location)
            self.queue.task_done()
