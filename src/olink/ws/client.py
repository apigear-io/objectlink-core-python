import asyncio
import websockets
from olink.client import ClientNode
from olink.core import EventHook
import logging


class Connection:
    def __init__(self, cancel: asyncio.Future, node: ClientNode):
        self._cancel = cancel
        self._node = node
        self._conn: websockets.WebSocketClientProtocol = None
        self._send_queue = asyncio.Queue()
        self.on_recv = EventHook()

    async def async_send(self, data):
        await self._conn.send(data)

    def send(self, data):
        self._send_queue.put_nowait(data)

    async def _sender(self):
        while True:
            msg = await self._send_queue.get()
            if self._cancel.done() and self._send_queue.empty():
                await self._conn.close()
                break
            await self._conn.send(msg)

    async def _receiver(self):
        try:
            async for data in self._conn:
                self.on_recv(data)
        except websockets.ConnectionClosed:
            pass

    async def connect(self, addr: str, done: asyncio.Future):
        async with websockets.connect(addr) as conn:
            logging.info("client connected")
            self._conn = conn
            receiver = asyncio.create_task(self._receiver())
            sender = asyncio.create_task(self._sender())
            logging.info("await client receiver, sender")
            _, pending = await asyncio.wait(
                [receiver, sender], return_when=asyncio.FIRST_COMPLETED
            )
            logging.info("client receiver, sender done")
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    def cancel(self):
        self._cancel.set_result(True)
        self._conn.close()
        self._conn = None
