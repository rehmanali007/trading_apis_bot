from selenium import webdriver
import json
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from models.global_enums import MessageTypes, Job


class BlogScraper:
    def __init__(self, message_queue):
        self.message_queue = message_queue
        f = open('config.json', 'r')
        self.config = json.load(f)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.loginfo = logging.getLogger(' Blog Scraper ').warning
        self.driver = webdriver.Chrome(executable_path=self.config.get(
            "CHROME_DRIVER_PATH"), options=options)
        self.blog_addr = 'https://blog.gather.network/'
        self.loop = asyncio.new_event_loop()
        self.itter_time = 1800

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        self.driver.get(self.blog_addr)
        self.latest_date = await self.get_latest_post_date()
        while True:
            self.loginfo('[+] Checking for new blog post ..')
            self.driver.refresh()
            ld = await self.get_latest_post_date()
            if ld == self.latest_date:
                await asyncio.sleep(self.itter_time)
                continue
            new_post = await self.get_new_post()
            message = await self.create_message(new_post)
            job = Job()
            job.message = message
            job.message_type = MessageTypes.TEXT_MESSAGE
            self.message_queue.put(job)
            await asyncio.sleep(self.itter_time)
            continue

    async def create_message(self, post):
        message = f'**{post["heading"]}**\n{post["text"]}\n**Date:** {post["date"]}\n[See Full Post]({post["link"]})'
        return message

    async def get_new_post(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, 'gt-blog-row'))
            )
        except:
            pass
        blog_row = self.driver.find_element_by_class_name('gt-blog-row')
        all_posts = blog_row.find_elements_by_class_name('postSecAre')
        latest_post = all_posts[0]
        latest_post_date = latest_post.find_element_by_class_name(
            'gt-blog-date').text
        date = latest_post_date.split('on')[-1].strip()
        heading = latest_post.find_element_by_tag_name('h2').text
        link = latest_post.find_element_by_tag_name('a').get_attribute('href')
        text = latest_post.text.split('\n')[2]
        post = {
            'date': date,
            'heading': heading,
            'text': text,
            'link': link
        }
        return post

    async def get_latest_post_date(self):
        try:
            WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located((By.ID, 'gt-blog-row'))
            )
        except:
            pass
        blog_row = self.driver.find_element_by_class_name('gt-blog-row')
        all_posts = blog_row.find_elements_by_class_name('postSecAre')
        latest_post = all_posts[0]
        latest_post_date = latest_post.find_element_by_class_name(
            'gt-blog-date').text
        date = latest_post_date.split('on')[-1].strip()
        return date


if __name__ == "__main__":
    import queue
    q = queue.Queue()
    scraper = BlogScraper(q)
    scraper.start()
