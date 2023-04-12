import asyncio
import websockets as ws
from olink.client import ClientNode


class Connection:
    def __init__(self, node=ClientNode()):
        self._node = node
        self._send_queue = asyncio.Queue()
        self._recv_queue = asyncio.Queue()
        self._conn: ws.WebSocketClientProtocol = None

    def send(self, msg):
        self._send_queue.put_nowait(msg)

    async def handle_send(self):
        while self._conn is not None:
            msg = await self._send_queue.get()
            data = self.serializer.serialize(msg)
            await self._conn.send(data)

    async def handle_recv(self):
        while self._conn is not None:
            msg = await self._recv_queue.get()
            self.emitter.emit(msg.object, msg)

    async def recv(self):
        async for data in self._conn:
            msg = self.serializer.deserialize(data)
            await self._recv_queue.put(msg)

    async def connect(self, addr: str):
        # connect to server
        async for conn in ws.connect(addr):
            try:
                self._conn = conn
                # start send and recv tasks
                await asyncio.gather(
                    self.handle_send(), self.handle_recv(), self.recv()
                )
            except ws.ConnectionClosed:
                continue

    def cancel(self):
        self._conn.close()
        self._conn = None
