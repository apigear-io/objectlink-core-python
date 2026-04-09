import asyncio
from asyncio.queues import Queue
from typing import Any

from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from olink.core.types import Name
from olink.remote import IObjectSource, RemoteNode


class CounterService:
    count = 0
    _node: RemoteNode

    def increment(self):
        self.count += 1
        self._node.notify_property_change("demo.Counter/count", self.count)


class CounterWebsocketAdapter(IObjectSource):
    # adapts the websocket communication to the remote source
    node: RemoteNode = None

    def __init__(self, impl):
        self.impl = impl
        self._methods = {"increment": impl.increment}
        self._properties = {"count": lambda v: setattr(impl, "count", v)}
        # register the source with the node registry
        RemoteNode.register_source(self)

    def olink_object_name(self):
        # return service name
        return "demo.Counter"

    def olink_invoke(self, name: str, args: list[Any]) -> Any:
        # handle the remote call from client node
        path = Name.path_from_name(name)
        func = self._methods.get(path)
        if func is None:
            return None
        return func(*args)

    def olink_set_property(self, name: str, value: Any):
        # set property value on implementation
        path = Name.path_from_name(name)
        setter = self._properties.get(path)
        if setter is not None:
            setter(value)

    def olink_linked(self, name: str, node: "RemoteNode"):
        # called when the source is linked to a client node
        self.impl._node = node

    def olink_unlinked(self, name: str):
        # called when the source is linked to a client node
        self.impl._node = None

    def olink_collect_properties(self) -> object:
        # collect properties from implementation to send back to client node initially
        return {k: getattr(self.impl, k) for k in ["count"]}


# create the service implementation
counter = CounterService()

# create the adapter for the implementation
adapter = CounterWebsocketAdapter(counter)


class RemoteEndpoint(WebSocketEndpoint):
    # endpoint to handle a client connection
    encoding = "text"

    def __init__(self, scope, receive, send):
        super().__init__(scope, receive, send)
        self.node = RemoteNode()
        self.queue = Queue()

    async def sender(self, ws):
        # sender coroutine, messages from queue are send to client
        print("start sender")
        while True:
            msg = await self.queue.get()
            print("send", msg)
            await ws.send_text(msg)
            self.queue.task_done()

    async def on_connect(self, ws: WebSocket):
        # handle a socket connection
        print("on_connect")
        # register a sender to the connection
        self._sender_task = asyncio.create_task(self.sender(ws))

        # a writer function to queue messages
        def writer(msg: str):
            print("write to queue:", msg)
            self.queue.put_nowait(msg)

        # register the writer function to the node
        self.node.on_write(writer)
        # call the super connection handler
        await super().on_connect(ws)

    async def on_receive(self, ws: WebSocket, data: Any) -> None:
        # handle a message from a client socket
        print("on_receive", data)
        self.node.handle_message(data)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        # handle a socket disconnect
        await super().on_disconnect(websocket, close_code)
        # remove the writer from the node
        self.node.on_write(None)
        # cancel the sender task to avoid deadlock
        self._sender_task.cancel()
        try:
            await self._sender_task
        except asyncio.CancelledError:
            pass


# see https://www.starlette.io/routing/
routes = [WebSocketRoute("/ws", RemoteEndpoint)]


# call with `uvicorn server:app --port 8282`
# see https://www.starlette.io
app = Starlette(routes=routes)
