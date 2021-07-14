import asyncio
from typing import Any
from asyncio.queues import Queue
from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from olink.core.types import Name
from olink.remotenode import IObjectSource, RemoteNode


class Counter:
    count = 0
    _node: RemoteNode
    def increment(self):
        self.count += 1
        self._node.notify_property_change('demo.Counter/count', self.count)

class CounterAdapter(IObjectSource):
    node: RemoteNode = None
    def __init__(self, impl):
        self.impl = impl
        RemoteNode.add_object_source(self)

    def olink_object_name(self):
        return 'demo.Counter'

    def olink_invoke(self, name: str, args: list[Any]) -> Any:
        path = Name.path_from_name(name)
        func = getattr(self.impl, path)
        func()

    def olink_set_property(self, name: str, value: Any):
        path = Name.path_from_name(name)
        setattr(self, self.impl, value)

    def olink_linked(self, name: str, node: "RemoteNode"):
        self.impl._node = node

    def olink_collect_properties(self) -> object:
        return {k: getattr(self.impl, k) for k in ['count']}

counter = Counter()
adapter = CounterAdapter(counter)




class RemoteEndpoint(WebSocketEndpoint):
    encoding = "text"
    node = RemoteNode()
    queue = Queue()

    async def sender(self, ws):
        print('start sender')
        while True:
            print('001')
            msg = await self.queue.get()
            print('send', msg)
            await ws.send_text(msg)
            self.queue.task_done()        

    async def on_connect(self, ws: WebSocket):
        print('on_connect')
        asyncio.create_task(self.sender(ws))

        def writer(msg: str):
            print('writer', msg)
            self.queue.put_nowait(msg)
        self.node.on_write(writer)
        await super().on_connect(ws)


    async def on_receive(self, ws: WebSocket, data: Any) -> None:
        print('on_receive', data)
        self.node.handle_message(data)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        await super().on_disconnect(websocket, close_code)
        self.node.on_write(None)
        await self.queue.join()



routes = [
    WebSocketRoute("/ws", RemoteEndpoint)
]

app = Starlette(routes=routes)