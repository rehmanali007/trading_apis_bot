import logging
import json
from telethon import TelegramClient
from queue import Queue
import asyncio
from models.global_enums import MessageTypes
from tg.fast_streams import upload_file
from io import BytesIO
import os
from models.global_enums import Job


class Sender:
    def __init__(self, client: TelegramClient, queue: Queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.client = client
        self.queue = queue
        self.latest_post = None
        self.loginfo = logging.getLogger(' Sender ').warning
        self.logerror = logging.getLogger(' Sender ').error
        self.target_channel = None

    def start(self):
        self.loginfo('[+] Starting sender ...')
        self.client.loop.create_task(self.main())

    async def main(self):
        while not self.client.is_connected():
            await asyncio.sleep(1)
        dialogs = await self.client.get_dialogs()
        for d in dialogs:
            if d.title == self.config.get("DEST_TG_CHANNEL_NAME"):
                self.loginfo('[+] Destination channel found!')
                self.target_channel = d
                break
        if self.target_channel is None:
            self.loginfo('[-] Destination channel not found!')
            exit()
        self.loginfo('[+] Message sender is ready!')
        while True:
            job: Job = self.queue.get()
            message_type = job.message_type
            if message_type == MessageTypes.TEXT_MESSAGE:
                await self.send_text_message(job.message)
            elif message_type == MessageTypes.GRAPH:
                await self.send_graph(job.graph_location)
            elif message_type == MessageTypes.PIN_MESSAGE:
                await self.send_pin_message(job.message)
            elif message_type == MessageTypes.REPOST:
                await self.repost_message()

            self.queue.task_done()

    async def send_text_message(self, message):
        sent = await self.client.send_message(self.target_channel, message)
        return sent

    async def send_graph(self, graph_location):
        self.loginfo('[+] Uploading the graph to channel ..')
        with open(graph_location, 'rb') as fh:
            buf = BytesIO(fh.read())
        uploaded_file = await self.client.upload_file(buf)
        await self.client.send_message(self.target_channel, file=uploaded_file)
        print('Graph sent to target channel!')
        os.remove(graph_location)

    async def send_pin_message(self, message):
        sent = await self.send_text_message(message)
        await self.client.pin_message(self.target_channel, sent)
        self.latest_post = message

    async def repost_message(self):
        print('Re-posting the message ...')
        if self.latest_post is None:
            return
        await self.send_text_message(self.latest_post)
