import websockets as ws
from typing import Any
import asyncio
from olink.remote import RemoteNode
import logging


class RemotePipe:
    def __init__(self, conn: ws.WebSocketServerProtocol):
        self._conn = conn
        self._node = RemoteNode()
        self._node.on_write(self._send)
        self._send_queue = asyncio.Queue()
        self._recv_queue = asyncio.Queue()

    def _send(self, data):
        self._send_queue.put_nowait(data)

    async def handle_send(self):
        while True:
            data = await self._send_queue.get()
            await self._conn.send(data)

    async def handle_recv(self):
        while True:
            data = await self._recv_queue.get()
            self._node.handle_message(data)

    async def recv(self):
        while True:
            data = await self._conn.recv()
            self._recv_queue.put_nowait(data)

    async def run(self):
        await asyncio.gather(
            self.handle_send(),
            self.handle_recv(),
            self.recv(),
        )


class Server:
    def __init__(self) -> None:
        self.pipes: list[RemotePipe] = []

    async def handle_connection(self, socket: ws.WebSocketServerProtocol):
        logging.info("New connection %s", socket)
        pipe = RemotePipe(socket)
        self.pipes.append(pipe)
        await pipe.run()

    async def serve(self, host: str, port: int):
        async with ws.serve(self.handle_connection, host, port):
            await asyncio.Future()  # run forever


def run_server(host: str, port: int):
    logging.info("Starting server on %s:%d", host, port)
    server = Server()
    asyncio.run(server.serve(host, port))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run_server("localhost", 8152)
