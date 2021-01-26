

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


class UserStream(tweepy.StreamListener):
    def __init__(self, config, queue):
        super().__init__()
        self.config = config
        self.queue = queue
        self.loginfo = logging.getLogger(' Twitter Stream ').warning
        self.logerror = logging.getLogger(' Twitter Stream ').error
        self.loop = new_event_loop()

    @staticmethod
    def getTime(created):
        data = created.split(' ')
        monthNumber = int(strptime(data[1], '%b').tm_mon)
        day = int(data[2])
        time = data[3].split(':')
        hours = int(time[0])
        minutes = int(time[1])
        year = int(data[-1])
        finalTime = dt(year, monthNumber, day, hours,
                       minutes) - timedelta(hours=5)
        new = finalTime.strptime(
            f'{finalTime.hour}:{finalTime.minute}', "%H:%M")
        new = new.strftime("%I:%M %p")
        final = f'{new} {finalTime.year}-{finalTime.month}-{finalTime.day}'
        return final

    def on_status(self, status):
        self.loginfo('Found a new tweet')
        username = status._json['user']['screen_name']
        usersList = list(self.config.get("TARGET_TWITTER_ACCOUNTS"))
        if f'@{username}' in usersList:
            tweet_text = status._json["text"]
            name = status._json['user']['name']
            tweet_id = status._json['id']
            tweet_link = f'https://twitter.com/i/web/status/{tweet_id}'
            message = f'**{name} just Tweeted!** \n{tweet_text}\n\n[See Full Tweet Here!]({tweet_link})'
            job = Job()
            job.message = message
            job.message_type = MessageTypes.TEXT_MESSAGE
            self.queue.put(job)
            self.loginfo('Tweet added to the queue!')

    def on_error(self, error):
        self.logerror('error found in twitter monitor', exc_info=True)
        self.loginfo(error)

    def on_disconnect(self, notice):
        self.loginfo('Disconnect notice')
        self.loginfo(notice)

    def on_exception(self, exception):
        self.logerror('Restarting the stream ..')
        return True


class Monitor:
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

    async def getHomeTimeLine(self):
        timeline = self.api.home_timeline()
        return timeline

    async def getUsersIDs(self, usersList):
        self.loginfo('Getting user ids')
        ids = []
        for user in usersList:
            userObj = self.api.get_user(user)
            ids.append(userObj._json.get('id_str'))
        return ids

    async def startStream(self):
        usersList = list(self.config.get("TARGET_TWITTER_ACCOUNTS"))
        idsList = await self.getUsersIDs(usersList)
        listener = UserStream(
            self.config, self.message_queue)
        stream = tweepy.Stream(auth=self.api.auth, listener=listener)

        async def restartStream():
            self.loginfo('[+] Starting the twitter stream ..')
            try:
                stream.filter(follow=idsList)
                self.loginfo('Twitter stream started!')
            except ProtocolError:
                await restartStream()
            except IncompleteRead:
                await restartStream()
        await restartStream()


if __name__ == "__main__":
    q = Queue()
    mon = Monitor(q)
    mon.start()
