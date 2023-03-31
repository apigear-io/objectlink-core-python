import asyncio
from typing import Any
from olink.core import Name
from .node import IObjectSink, ClientNode
from olink.core.hook import EventHook


class AbstractSink(IObjectSink):
    on_property_changed = EventHook()
    object_id: str = None

    client = None

    def __init__(self, object_id: str):
        self.object_id = object_id
        self.client = ClientNode.register_sink(self)

    async def _invoke(self, name, args):
        future = asyncio.get_running_loop().create_future()
        def func(args):
            return future.set_result(args.value)
        self.client.invoke_remote(f'{self.object_id}/{name}', args, func)
        return await asyncio.wait_for(future, 500)

    def olink_object_name(self):
        return self.object_id

    def olink_on_init(self, name: str, props: object, node: ClientNode):        
        for k in props:
            setattr(self, k, props[k])

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        path = Name.path_from_name(name)
        setattr(self, name, value)
        self.on_property_changed.fire(path, value)

    def olink_on_signal(self, name: str, args: list[Any]):
        path = Name.path_from_name(name)
        hook = getattr(self, f'on_{path}')        
        hook.fire(*args)
