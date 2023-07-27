from typing import Any
from olink.core import Protocol, BaseNode
from .registry import RemoteRegistry, get_remote_registry
from .source import IObjectSource

class RemoteNode(BaseNode):
    # a remote node is a node that is linked to a remote source
    def __init__(self):
        # initialise node and attaches this node to registry
        super().__init__()

    def detach(self):
        # detach this node from registry
        self.registry().remove_node(self)

    def handle_link(self, name: str) -> None:
        # handle link message from client node
        # sends init message to client node
        source = RemoteNode.get_source(name)
        if source:
            self.registry().add_node_to_source(name, self)
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
            # only send reply for not empty values
            if value:
                self.emit_write(Protocol.invoke_reply_message(id, name, value))

    def registry(self) -> RemoteRegistry:
        # returns global registry
        return get_remote_registry()

    @staticmethod
    def get_source(name) -> IObjectSource:
        # get object source from registry
        return get_remote_registry().get_source(name)

    @staticmethod
    def register_source(source: IObjectSource):
        # add object source to registry
        return get_remote_registry().add_source(source)

    @staticmethod
    def unregister_source(source: IObjectSource):
        # remove object source from registry
        return get_remote_registry().remove_source(source)

    @staticmethod
    def notify_property_change(name: str, value: Any) -> None:
        # notify property change to all named client nodes
        for node in get_remote_registry().get_nodes(name):
            node.emit_write(Protocol.property_change_message(name, value))

    @staticmethod
    def notify_signal(name: str, args: list[Any]):
        # notify signal to all named client nodes
        for node in get_remote_registry().get_nodes(name):
            node.emit_write(Protocol.signal_message(name, args))
