from asyncio.queues import Queue
from typing import Any
from olink.core.types import Name
from olink.clientnode import IObjectSink, ClientNode
import asyncio
import websockets

class Counter(IObjectSink):
    count = 0
    client = None
    def __init__(self):
        self.client = ClientNode.register_sink(self)
        print('client', self.client)

    def increment(self):
        if self.client:
            self.client.invoke_remote('demo.Counter/increment', [], None)

    def olink_object_name(self):
        return 'demo.Counter'

    def olink_on_signal(self, name: str, args: list[Any]):
        path = Name.path_from_name(name)
        print('on signal: %s: %s' % (path, args))

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        path = Name.path_from_name(name)
        print('on property changed: %s: %s' % (path, value))

    def olink_on_init(self, name: str, props: object, node: ClientNode):
        print('on init: %s: %s' % (name, props))
        self.client = node
        
    def olink_on_release(self):
        print('on release')
    

async def sender(ws, q):
    while True:
        data = await q.get()
        await ws.send_text(data)
        q.task_done()


async def connect(address: str):
    node = ClientNode()
    queue = Queue()
    async with websockets.connect(address) as ws:
        def writer(msg: str):
            queue.put_nowait(msg)
        node.on_write(writer)
        while True:
            data = await ws.recv()
            node.handle_message(data)

class Client:
    queue = Queue()
    node = None
    def __init__(self, node):
        self.node = node
        self.node.on_write(self.writer)

    def writer(self, data):
        print('writer, data')
        self.queue.put_nowait(data)

    async def _reader(self, ws):
        while True:
            data = await ws.recv()
            self.node.handle_message(data)
    
    async def _sender(self, ws):
        while True:
            data = await self.queue.get()
            await ws.send(data)
            self.queue.task_done()

    async def connect(self, address: str):
        async with websockets.connect(address) as ws:
            print('connected')
            sender_task = asyncio.create_task(self._sender(ws))
            reader_task = asyncio.create_task(self._reader(ws))
            await asyncio.gather(sender_task, reader_task)
            await self.queue.join()



address = 'ws://localhost:8282/ws'
node = ClientNode()
node.link_node('demo.Counter')
client = Client(node)

counter = Counter()
node.link_remote('demo.Counter')
counter.increment()
asyncio.get_event_loop().run_until_complete(client.connect(address))
