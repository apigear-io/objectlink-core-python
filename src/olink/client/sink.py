import asyncio
from typing import Any
from olink.core import Name
from .node import IObjectSink, ClientNode
from olink.core.hook import EventHook


class AbstractSink(IObjectSink):
    def __init__(self, object_id: str):
        self._object_id = object_id
        self.on_property_changed = EventHook()
        self._node: ClientNode = None

    async def _invoke(self, name, args):
        future = asyncio.get_running_loop().create_future()

        def func(args):
            return future.set_result(args.value)

        self.get_node().invoke_remote(f"{self._object_id}/{name}", args, func)
        return await asyncio.wait_for(future, 500)

    def olink_object_name(self):
        return self._object_id

    def olink_on_init(self, name: str, props: object, node: ClientNode):
        self._node = node
        for k in props:
            setattr(self, k, props[k])

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        path = Name.path_from_name(name)
        setattr(self, name, value)
        self.on_property_changed.fire(path, value)

    def olink_on_signal(self, name: str, args: list[Any]):
        path = Name.path_from_name(name)
        hook = getattr(self, f"on_{path}")
        hook.fire(*args)

    def get_node(self) -> ClientNode:
        if self._node is None:
            raise Exception("Sink not linked to node")
        return self._node
