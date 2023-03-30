import websockets as ws
from .emitter import Emitter
from typing import Any
import asyncio
from .client import Client
from ..remotenode import IObjectSource, RemoteNode

class SourceAdapter(IObjectSource):
    node: RemoteNode = None
    object_id: str = None
    def __init__(self, objectId: str, impl) -> None:
        self.object_id = objectId
        self.impl = impl
        RemoteNode.register_source(self)

    def olink_object_name() -> str:
        return self.objectId
    
    def olink_invoke(self, name: str, args: list[Any]) -> Any:
        path = Name.path_from_name(name)
        func = getattr(self.impl, path)
        try:
            result = func(**args)
        except Exception as e:
            print('error: %s' % e)
            result = None
        return result
    
    def olink_set_property(self, name: str, value: Any):
        # set property value on implementation
        path = Name.path_from_name(name)
        setattr(self, self.impl, value)

    def olink_linked(self, name: str, node: "RemoteNode"):
        # called when the source is linked to a client node
        self.node = node

    def olink_collect_properties(self) -> object:
        # collect properties from implementation to send back to client node initially
        return {k: getattr(self.impl, k) for k in ['count']}


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
