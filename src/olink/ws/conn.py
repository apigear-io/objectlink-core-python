import asyncio
from pyee.asyncio import AsyncIOEventEmitter
import logging
import websockets as ws

log = logging.getLogger(__name__)


class Connection(AsyncIOEventEmitter):
    def __init__(
        self, cancel: asyncio.Event, socket: ws.WebSocketServerProtocol = None
    ):
        super().__init__()
        self._cancel = cancel
        self._socket = socket
        self._send_queue = asyncio.Queue()
        self._receiver_task = None
        self._sender_task = None
        if socket:  # we are server
            log.info("server conn init")
            self._receiver_task = asyncio.create_task(
                self._receiver(), name="server conn receiver"
            )
            self._sender_task = asyncio.create_task(
                self._sender(), name="server conn sender"
            )

    async def connect(self, addr: str):
        log.info("client connected")
        async with ws.connect(addr) as self._socket:
            self._receiver_task = asyncio.create_task(
                self._receiver(), name="client receiver"
            )
            self._sender_task = asyncio.create_task(
                self._sender(), name="client sender"
            )

    async def _sender(self):
        while not self._cancel.is_set():
            try:
                msg = await self._send_queue.get()
                if not msg:
                    log.info("sender got None, closing")
                    break
                await self._socket.send(msg)
                self._send_queue.task_done()
            except Exception as e:
                log.info("connection sender closing: %s", e)
                break
        log.info("sender done")

    async def _receiver(self):
        while not self._cancel.is_set():
            try:
                msg = await self._socket.recv()
                self.emit("message", msg)
            except Exception:
                log.info("Connection closed")
                break
        log.info("receiver done")

    def send(self, data):
        self._send_queue.put_nowait(data)

    async def send_async(self, data):
        await self._send_queue.put(data)

    async def cancel(self):
        self._cancel.set()
        if self._socket:
            await self._socket.close()
        self._socket = None
        self._send_queue.put_nowait(None)
        if self._receiver_task:
            await self._receiver_task
        if self._sender_task:
            await self._sender_task
        self._receiver_task = None
        self._sender_task = None
