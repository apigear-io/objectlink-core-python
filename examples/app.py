from asyncio.queues import Queue
from typing import Any
from olink.core.types import Name
from olink.clientnode import IObjectSink, ClientNode
import asyncio
import websockets


class CounterSink(IObjectSink):
    # this is the sink for the counter
    count = 0
    client = None

    def __init__(self):
        # register sink with client node
        self.client = ClientNode.register_sink(self)
        print("client", self.client)

    def increment(self):
        # remote call the increment method
        if self.client:
            self.client.invoke_remote("demo.Counter/increment", [], None)

    def olink_object_name(self):
        # return the name of the sink
        return "demo.Counter"

    def olink_on_signal(self, name: str, args: list[Any]):
        # handle the incoming signal from the remote source
        path = Name.path_from_name(name)
        print("on signal: %s: %s" % (path, args))

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        # handle the property change from the remote source
        path = Name.path_from_name(name)
        print("on property changed: %s: %s" % (path, value))

    def olink_on_init(self, name: str, props: object, node: ClientNode):
        # handle the initialization of the sink,
        # called when the sink is linked to remote source
        print("on init: %s: %s" % (name, props))
        self.client = node

    def olink_on_release(self):
        # handle the release of the sink,
        # called when the sink is unlinked from remote source
        print("on release")


class ClientWebsocketAdapter:
    # adapts the websocket communication to the client node
    queue = Queue()
    node = None

    def __init__(self, node):
        self.node = node
        # register a write function
        self.node.on_write(self.writer)

    def writer(self, data):
        # don't send directly, first write to queue
        print("write to queue")
        self.queue.put_nowait(data)

    async def _reader(self, ws):
        # handle incoming ws messages
        while True:
            msg = await ws.recv()
            self.node.handle_message(msg)

    async def _sender(self, ws):
        # send messages from queue
        while True:
            data = await self.queue.get()
            await ws.send(data)
            self.queue.task_done()

    async def connect(self, address: str):
        # connect to websocket server
        async for ws in websockets.connect(address):
            # connect might fail so loop continuously, for a retry-connection
            # see https://websockets.readthedocs.io/en/stable/reference/client.html#opening-a-connection
            try:
                sender_task = asyncio.create_task(self._sender(ws))
                reader_task = asyncio.create_task(self._reader(ws))
                await asyncio.gather(sender_task, reader_task)
                await self.queue.join()
            except Exception as e:
                print("exception while connecting: ", e)


address = "ws://localhost:8282/ws"
# create a client node for ObjectLink registry and protocol
node = ClientNode()
# link the node to the service name
node.link_node("demo.Counter")

# create a ws client which handles the ws adapter
client = ClientWebsocketAdapter(node)

counter = CounterSink()
node.link_remote("demo.Counter")
counter.increment()


async def countForever():
    # every send increment the counter
    while True:
        await asyncio.sleep(1)
        counter.increment()


# await both tasks to complete
future = asyncio.gather(client.connect(address), countForever())
# get the event loop
loop = asyncio.get_event_loop()
# run the event loop until future completes
loop.run_until_complete(future)
