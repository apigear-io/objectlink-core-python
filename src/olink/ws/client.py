import asyncio
import websockets as ws
from olink.client import ClientNode

class Connection:
    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()
    node = None
    def __init__(self, node=ClientNode()):
        self.node = node

    def send(self, msg):
        self.send_queue.put_nowait(msg)

    async def handle_send(self):
        async for msg in self.send_queue:
            data = self.serializer.serialize(msg)
            await self.conn.send(data)

    async def handle_recv(self):
        async for msg in self.recv_queue:
            self.emitter.emit(msg.object, msg)

    async def recv(self):
        async for data in self.conn:
            msg = self.serializer.deserialize(data)
            self.recv_queue.put_nowait(msg)

    async def connect(self, addr: str):
        # connect to server
        async for conn in ws.connect(addr):
            self.conn = conn
            # start send and recv tasks
            await asyncio.gather(self.handle_send(), self.handle_recv(), self.recv())
            # wait for all queues to be empty
            await self.send_queue.join()
            await self.recv_queue.join()