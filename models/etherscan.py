from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import asyncio
import re


class Etherscan:
    def __init__(self):
        f = open('config.json', 'r')
        self.config = json.load(f)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36")
        self.driver = webdriver.Chrome(
            executable_path=self.config.get("CHROME_DRIVER_PATH"), options=options)
        self.target_url = 'https://etherscan.io/token/0xc3771d47E2Ab5A519E2917E61e23078d0C05Ed7f#balances'
        self.loop = asyncio.new_event_loop()
        self.itter_time = 3600
        self.driver.get(self.target_url)

    def get_holders(self):
        while True:
            self.driver.refresh()
            holders_data_div = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.ID, "ContentPlaceHolder1_tr_tokenHolders"))
            )
            holders = holders_data_div.text.split('\n')[1].split(' ')[0]
            holders = holders.replace(',', '')
            yield holders


if __name__ == "__main__":
    eth = Etherscan()
    get_holders = eth.get_holders()
    print(next(get_holders))
