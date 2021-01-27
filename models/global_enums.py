import enum


class MessageTypes(enum.Enum):
    TEXT_MESSAGE = 'text message'
    GRAPH = 'Graph'
    PIN_MESSAGE = 'pin message'
    REPOST = 'repost'


class Threads(enum.Enum):
    HOO = 'HOO'
    GATE = 'GATE'
    UNISWAP = 'UNISWAP'
    BITHUMB = 'BITHUMB'


class Signal:
    def __init__(self, source):
        self.source = source
        self.is_data_ready = False
        self.is_data_sent = False
        self.is_fetching_data = False


class Synchronizer:
    def __init__(self):
        self.hoo_data_ready = False
        self.gate_data_ready = False
        self.uniswap_data_ready = False
        self.bithumb_data_ready = False
        self.all_data_ready = False
        self.hoo_data_sent = False
        self.gate_data_sent = False
        self.uniswap_data_sent = False
        self.bithumb_data_sent = False
        self.can_fetch_data = True
        self.hoo_fetching_data = False
        self.uniswap_fetching_data = False
        self.gate_fetching_data = False
        self.bithumb_fetching_data = False
        self.all_data_sent = False


class Job:
    def __init__(self, message_type: MessageTypes = None,
                 message: str = None, graph_location: str = None):
        self.message_type = MessageTypes
        self.message = message
        self.graph_location = graph_location

    def __repr__(self):
        return self.message


if __name__ == '__main__':
    job = Job()
    job.message = 'Message is here'
    job.message_type = MessageTypes.REPOST
    print(job.message_type)
