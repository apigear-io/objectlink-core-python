import websockets as ws
from typing import Any
import asyncio
from olink.remote import RemoteNode, RemoteRegistry
import logging
from .conn import Connection


class RemoteHandler:
    def __init__(self, conn: Connection, node: RemoteNode) -> None:
        self.conn = conn
        self.node = node
        self.conn.on("message", self.on_recv_message)
        self.node.on_write(self.on_send_message)

    def on_recv_message(self, msg: str):
        self.node.handle_message(msg)

    def on_send_message(self, msg: str):
        self.conn.send(msg)

    async def cancel(self):
        await self.conn.cancel()
        self.node.detach()


class Server:
    def __init__(self, cancel: asyncio.Event) -> None:
        logging.info("server init")
        self._cancel = cancel
        self._handlers: list[RemoteHandler] = []
        self._registry = RemoteRegistry()

    async def _handler(self, socket: ws.WebSocketServerProtocol):
        logging.info("server handle new connection %s", socket)
        node = RemoteNode(self._registry)
        conn = Connection(self._cancel, socket)
        handler = RemoteHandler(conn, node)
        self._handlers.append(handler)

    async def serve(self, host: str, port: int):
        logging.info("server serve")
        async with ws.serve(self._handler, host, port):
            await self._cancel.wait()
            logging.info("server cancel wait done")

    async def cancel(self):
        logging.info("server cancel")
        for handler in self._handlers:
            await handler.cancel()
        self._cancel.set()
