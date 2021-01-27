import asyncio
import threading
from models.global_enums import Threads
from models.global_enums import Synchronizer


class ControlThread:
    def __init__(self, queue, sync: Synchronizer):
        self.queue = queue
        self.sync = sync
        self.loop = asyncio.new_event_loop()

    def start(self):
        self.loop.run_until_complete(self.main())

    def all_data_ready(self):
        if not self.sync.hoo_data_ready:
            return False
        if not self.sync.uniswap_data_ready:
            return False
        if not self.sync.bithumb_data_ready:
            return False
        if not self.sync.gate_data_ready:
            return False
        return True

    def all_data_sent(self):
        if not self.sync.gate_data_sent:
            return False
        if not self.sync.uniswap_data_sent:
            return False
        if not self.sync.hoo_data_sent:
            return False
        if not self.sync.bithumb_data_sent:
            return False
        return True

    def anyone_fetching_data(self):
        if self.sync.bithumb_fetching_data:
            return True
        if self.sync.hoo_fetching_data:
            return True
        if self.sync.uniswap_fetching_data:
            return True
        if self.sync.gate_fetching_data:
            return True
        return False

    async def main(self):
        while True:
            signal = self.queue.get()
            if signal.source == Threads.HOO:
                self.sync.hoo_data_ready = signal.is_data_ready
                self.sync.hoo_data_sent = signal.is_data_sent
                self.sync.hoo_fetching_data = signal.is_fetching_data
            elif signal.source == Threads.UNISWAP:
                self.sync.uniswap_data_ready = signal.is_data_ready
                self.sync.uniswap_data_sent = signal.is_data_sent
                self.sync.uniswap_fetching_data = signal.is_fetching_data
            elif signal.source == Threads.BITHUMB:
                self.sync.bithumb_data_ready = signal.is_data_ready
                self.sync.bithumb_data_sent = signal.is_data_sent
                self.sync.bithumb_fetching_data = signal.is_fetching_data
            elif signal.source == Threads.GATE:
                self.sync.gate_data_ready = signal.is_data_ready
                self.sync.gate_data_sent = signal.is_data_sent
                self.sync.gate_fetching_data = signal.is_fetching_data
            if self.anyone_fetching_data():
                self.sync.all_data_ready = False
                self.sync.all_data_sent = False
            if self.all_data_ready():
                self.sync.all_data_ready = True
                self.sync.can_fetch_data = True
            if self.all_data_ready() and self.all_data_sent():
                self.sync.all_data_sent = True
                self.can_fetch_data = True
