from selenium import webdriver
import json
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
from models.global_enums import MessageTypes, Job


class FetchGraph:
    def __init__(self, graph_queue):
        self.graph_queue = graph_queue
        self.loginfo = logging.getLogger(' Graph ').info
        f = open('config.json', 'r')
        self.config = json.load(f)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("--start-maximized")
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        options.add_argument(f'--user-agent={user_agent}')
        self.driver = webdriver.Chrome(executable_path=self.config.get(
            "CHROME_DRIVER_PATH"), options=options)
        self.target_addr = 'https://www.bithumb.pro/en-us/spot/trade?q=GTH-USDT'
        self.loop = asyncio.new_event_loop()
        self.root = os.getcwd()
        self.screenshots_location = f'{self.root}/graphs_as_pngs'
        if not os.path.exists(self.screenshots_location):
            os.makedirs(self.screenshots_location)
        self.screenshot = f'{self.screenshots_location}/latest_graph.png'
        self.logger = logging.getLogger(' Graph Fetcher ').warning
        self.itter_time = 1800

    def start(self):
        self.loop.run_until_complete(self.main())

    async def main(self):
        self.driver.get(self.target_addr)
        while True:
            self.logger('[+] Reloading website ...')
            self.driver.refresh()
            dark_mode = False
            while not dark_mode:
                theme_change = self.driver.find_element_by_class_name(
                    'theme-exchange-component')
                theme_change.click()
                classes = theme_change.get_attribute('class').split(' ')
                if 'dark' in classes:
                    dark_mode = True
                await asyncio.sleep(0.5)
            try:
                frame = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.TAG_NAME, 'iframe'))
                )
            except:
                continue
            frame = self.driver.find_element_by_tag_name('iframe')
            self.driver.switch_to.frame(frame)
            try:
                chart = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'chart-page'))
                )
            except:
                continue
            try:
                time_buttons = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, "dropdown-menu-item"))
                )
            except:
                continue
            time_buttons = self.driver.find_elements_by_class_name(
                'dropdown-menu-item')
            for btn in time_buttons:
                attr = btn.get_attribute('data-title')
                if attr == '30M':
                    btn.click()
                    break
            await asyncio.sleep(3)
            if os.path.exists(self.screenshot):
                os.remove(self.screenshot)
            data = chart.screenshot_as_png
            ss = open(self.screenshot, 'wb')
            ss.write(data)
            ss.close()
            self.logger('[+] Graph Captured!')
            job = Job()
            job.graph_location = self.screenshot
            job.message_type = MessageTypes.GRAPH
            self.graph_queue.put(job)
            await asyncio.sleep(self.itter_time)


if __name__ == "__main__":
    import queue
    q = queue.Queue()
    scraper = FetchGraph(q)
    scraper.start()
