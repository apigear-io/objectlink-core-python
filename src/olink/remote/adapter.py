from typing import Any
from olink.core.types import Name
from .node import RemoteNode
from .types import IObjectSource
import logging


class SourceAdapter(IObjectSource):
    def __init__(self, objectId: str, impl) -> None:
        self._object_id = objectId
        self.impl = impl
        self.impl._change += self.on_change
        self.impl._emit += self.on_emit
        self._node: RemoteNode = None

    def on_emit(self, path: str, args: list[Any]):
        name = Name.create_name(self._object_id, path)
        RemoteNode.notify_signal(name, args)

    def on_change(self, name: str, value: Any):
        name = Name.create_name(self._object_id, name)
        RemoteNode.notify_property_changed(name, value)

    def olink_object_name(self) -> str:
        return self._object_id

    def olink_invoke(self, name: str, args: list[Any]) -> Any:
        path = Name.path_from_name(name)
        func = getattr(self.impl, path)
        try:
            result = func(*args)
        except Exception as e:
            logging.exception(e)
            print("error: %s" % e)
            result = None
            raise e
        return result

    def olink_set_property(self, name: str, value: Any):
        # set property value on implementation
        path = Name.path_from_name(name)
        setattr(self.impl, path, value)

    def olink_linked(self, name: str, node: "RemoteNode"):
        # called when the source is linked to a client node
        self._node = node

    def olink_collect_properties(self) -> object:
        # collect properties from implementation to send back to client node initially
        return {k: getattr(self.impl, k) for k in ["count"]}
