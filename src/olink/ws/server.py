import websockets as ws
from typing import Any
import asyncio
from olink.remote import RemoteNode



class RemotePipe:
    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()
    node = RemoteNode()
    def __init__(self, conn: ws.ClientConnection):
        self.conn = conn
        self.node.on_write(self._send)

    def _send(self, data):
        self.send_queue.put_nowait(data)

    async def handle_send(self):
        async for data in self.send_queue:
            await self.conn.send(data)

    async def handle_recv(self):
        async for data in self.recv_queue:
            self.node.handle_message(data)

    async def recv(self):
        async for data in self.conn:
            self.recv_queue.put_nowait(data)

class Server:
    pipes = []
    def handle_connection(self, pipe: ws.WebSocketServerProtocol, path: str):
        pipe = RemotePipe(pipe, self.serializer)
        self.pipes.append(pipe)

    async def serve(self, host: str, port: int):
        async with ws.serve(self.handle_connection, host, port):
            await asyncio.Future()




def run_server(host: str, port: int):
    server = Server()
    asyncio.run(server.serve(host, port))


if __name__ == "__main__":
    run_server("localhost", 8152)
