import enum


class MessageTypes(enum.Enum):
    TEXT_MESSAGE = 'text message'
    GRAPH = 'Graph'
    PIN_MESSAGE = 'pin message'
    REPOST = 'repost'


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
