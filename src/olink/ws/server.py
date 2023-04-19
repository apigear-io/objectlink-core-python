import websockets
from typing import Any
import asyncio
from olink.remote import RemoteNode, RemoteRegistry
import logging


class RemotePipe:
    def __init__(
        self,
        cancel: asyncio.Future,
        node: RemoteNode,
        conn: websockets.WebSocketServerProtocol,
    ):
        self._cancel = cancel
        self._conn = conn
        self._node = node
        self._node.on_write(self._send)
        self._send_queue = asyncio.Queue()

    def _send(self, data):
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
            async for msg in self._conn:
                self._node.handle_message(msg)
        except websockets.ConnectionClosed:
            logging.info("Connection closed")
            pass

    async def run(self):
        receiver = asyncio.create_task(self._receiver())
        sender = asyncio.create_task(self._sender())
        _, pending = await asyncio.wait(
            [receiver, sender], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logging.info("Task cancelled")
                pass

    def cancel(self):
        if self._cancel:
            self._cancel.set_result(True)


class Server:
    def __init__(self, cancel: asyncio.Future) -> None:
        logging.info("server init")
        self._cancel = cancel
        self.pipes: list[RemotePipe] = []
        self._registry = RemoteRegistry()

    async def _handler(self, conn: websockets.WebSocketServerProtocol):
        logging.info("server handle new connection %s", conn)
        node = RemoteNode(self._registry)
        pipe = RemotePipe(self._cancel, node, conn)
        self.pipes.append(pipe)
        await pipe.run()

    async def serve(self, host: str, port: int):
        logging.info("server serve")
        async with websockets.serve(self._handler, host, port):
            await self._cancel

    async def cancel(self):
        logging.info("server cancel")
        for pipe in self.pipes:
            pipe.cancel()
        self._cancel.set_result(True)


async def run_server(cancel: asyncio.Future, host: str, port: int):
    logging.info("run server on %s:%d", host, port)
    server = Server(cancel)
    logging.info("await serve")
    await server.serve(host, port)
    print("run_server done")
    server.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(run_server("localhost", 8152))
