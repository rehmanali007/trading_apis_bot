import json
import tweepy
from queue import Queue
from asyncio import sleep, new_event_loop
import asyncio
import logging
import re
from pprint import pprint
from time import strptime, strftime, struct_time
from datetime import datetime as dt, timedelta
import aiohttp
from urllib3.exceptions import ProtocolError
from http.client import IncompleteRead
from models.global_enums import MessageTypes, Job
import urllib3
from APIs.utils import get_fire_emojies

COUNTER = 0


class UserStream(tweepy.StreamListener):
    def __init__(self, config, queue):
        super().__init__()
        self.config = config
        self.queue = queue
        self.loginfo = logging.getLogger(' Tweets Counter ').warning
        self.logerror = logging.getLogger(' Tweets Counter ').error
        self.loop = new_event_loop()
        self.target_time = dt.utcnow() + timedelta(minutes=15)

    def on_status(self, status):
        global COUNTER
        COUNTER += 1
        time_now = dt.utcnow()
        print(f'$GTH Mention : {COUNTER}')
        if time_now < self.target_time:
            return True
        fire_emojies = get_fire_emojies(COUNTER)
        message = f'**15 Minute GTH Twitter Mention Report**\n\n**Total $GTH Mentions :** {COUNTER}\n{fire_emojies}'
        job = Job()
        job.message = message
        job.message_type = MessageTypes.TEXT_MESSAGE
        self.queue.put(job)
        COUNTER = 0
        self.target_time = dt.utcnow() + timedelta(minutes=15)

    def on_connect(self):
        print(' [+] GTH counter is ready!')

    def on_error(self, error):
        self.logerror(
            'Some error in GTH counter ..\nRestarting the counter ....', exc_info=True)
        self.loginfo(error)

    def on_disconnect(self, notice):
        self.loginfo('Disconnect notice')
        self.loginfo(notice)

    def on_exception(self, exception):
        self.logerror('Restarting the stream ..')
        return True


class WordCounter:
    def __init__(self, message_queue):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.loginfo = logging.getLogger(' Twitter Monitor ').warning
        self.logerror = logging.getLogger(' Twitter Monitor ').error
        auth = tweepy.OAuthHandler(self.config.get(
            'TWITTER_API_KEY'), self.config.get('TWITTER_API_KEY_SECRET'))
        auth.set_access_token(self.config.get(
            "TWITTER_ACCESS_TOKEN"), self.config.get('TWITTER_ACCESS_TOKEN_SECRET'))
        self.api = tweepy.API(auth)
        self.loop = new_event_loop()
        self.message_queue = message_queue

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        await self.startStream()

    async def startStream(self):
        listener = UserStream(
            self.config, self.message_queue)
        stream = tweepy.Stream(auth=self.api.auth, listener=listener)

        async def restartStream():
            self.loginfo('[+] Starting the twitter stream ..')
            try:
                trackList = ['$GTH', '$gth', '$Gth', '$gTh',  '$gtH']
                try:
                    stream.filter(track=trackList)
                except urllib3.exceptions.ReadTimeoutError:
                    await asyncio.sleep(3)
                    return await self.startStream()
                self.loginfo('Twitter stream started!')
            except ProtocolError:
                await restartStream()
            except IncompleteRead:
                await restartStream()
        await restartStream()


if __name__ == "__main__":
    q = Queue()
    mon = WordCounter(q)
    mon.start()
