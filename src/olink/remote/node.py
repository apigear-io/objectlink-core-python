from olink.core import BaseNode, Name, Protocol
from typing import Any
from .registry import RemoteRegistry
from .types import IObjectSource


class RemoteNode(BaseNode):
    def __init__(self, registry: RemoteRegistry):
        # initialise node and attaches this node to registry
        super().__init__()
        self._registry = registry

    def detach(self):
        # detach this node from registry
        self.registry().remove_node(self)

    def handle_link(self, name: str) -> None:
        # handle link message from client node
        # sends init message to client node
        source = self.get_source(name)
        if source:
            self.registry().add_node(name, self)
            source.olink_linked(name, self)
            props = source.olink_collect_properties()
            self.emit_write(Protocol.init_message(name, props))

    def handle_unlink(self, name: str):
        # unlinks names source from registry
        source = self.get_source(name)
        if source:
            self.registry().remove_node_from_source(name, self)

    def handle_set_property(self, name: str, value: Any):
        # handle set property message from client node
        # calls set property on source
        source = self.get_source(name)
        if source:
            source.olink_set_property(name, value)

    def handle_invoke(self, id: int, name: str, args: list[Any]) -> None:
        # handle invoke message from client node
        # calls invoke on source
        # returns invoke reply message to client node
        source = self.get_source(name)
        if source:
            value = source.olink_invoke(name, args)
            self.emit_write(Protocol.invoke_reply_message(id, name, value))

    def registry(self) -> RemoteRegistry:
        return self._registry

    def get_source(self, name: str) -> IObjectSource:
        return self.registry().get_source(name)

    def notify_property_changed(self, name: str, value: Any) -> None:
        self.registry().notify_property_changed(name, value)

    def notify_signal(self, name: str, args: list[Any]) -> None:
        self.registry().notify_signal(name, args)
