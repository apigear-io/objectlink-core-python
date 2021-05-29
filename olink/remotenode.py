from olink.core.protocol import Protocol
from olink.core.types import Base, LogLevel, Name
from olink.core.node import BaseNode

from typing import Any, Protocol as ProtocolType

class IObjectSource(ProtocolType):
    def olink_object_name() -> str:
        raise NotImplementedError()

    def olink_invoke(self, name: str, args: list[Any]):
        raise NotImplementedError()

    def olink_set_property(self, name: str, value: Any):
        raise NotImplementedError()

    def olink_linked(self, name: str, node: "RemoteNode"):
        raise NotImplementedError()

    def olink_collect_properties(self) -> object:
        raise NotImplementedError()


class SourceToNodeEntry:
    source: IObjectSource = None
    nodes: set["RemoteNode"] = set()

    def __init__(self, source=None):
        self.source = source
        self.nodes = set()



class RemoteRegistry(Base):
    entries: dict[str, SourceToNodeEntry] = {}

    def add_object_source(self, source: IObjectSource):
        name = source.olink_object_name()
        self.emit_log(LogLevel.DEBUG, f"RemoteRegistry.add_object_source: {name}")
        self.entry(name).source = source

    def remove_object_source(self, source: IObjectSource):
        name = source.olink_object_name()
        self.remove_entry(name)
    
    def get_object_source(self, name: str):
        return self.entry(name).source
    
    def get_remote_nodes(self, name: str):
        return self.entry(name).nodes
    
    def attach_remote_node(self, node: "RemoteNode"):
        self.emit_log(LogLevel.DEBUG, "RemoteRegistry.attach_remote_node")

    def detach_remote_node(self, node: "RemoteNode"):
        self.emit_log(LogLevel.DEBUG, "RemoteRegistry.detach_remote_node")
        for entry in self.entries.values():
            if node in entry.nodes:
                entry.nodes.remove(node)

    def link_remote_node(self, name: str, node: "RemoteNode"):
        self.entry(name).nodes.add(node)

    def unlink_remote_node(self, name: str, node: "RemoteNode"):
        self.entry(name).nodes.remove(node)

    def entry(self, name: str) -> SourceToNodeEntry:
        resource = Name.resource_from_name(name)
        if not resource in self.entries:
            self.emit_log(LogLevel.DEBUG, f"add new resource: {resource}")
            self.entries[resource] = SourceToNodeEntry()
        return self.entries[resource]

    def remove_entry(self, name: str) -> None:
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            del self.entries[resource]
        else:
            self.emit_log(LogLevel.DEBUG, f'remove resource failed, resource not exists: {resource}')


    def has_entry(self, name: str) -> SourceToNodeEntry:
        resource = Name.resource_from_name(name)
        return resource in self.entries

    def init_entry(self, name: str):
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            self.entries[resource] = SourceToNodeEntry()



    def clear(self):
        self.entries = {}

_registry = RemoteRegistry()

class RemoteNode(BaseNode):
    def __init__(self):
        super().__init__()
        _registry.attach_remote_node(self)

    def detach(self):
        _registry.detach_remote_node(self)

    def registry(self) -> RemoteRegistry:
        return _registry

    def get_object_source(self, name) -> IObjectSource:
        return self.registry().get_object_source(name)

    @staticmethod
    def add_object_source(source: IObjectSource):
        return _registry.add_object_source(source)

    @staticmethod
    def remove_object_source(source: IObjectSource):
        return _registry.remove_object_source(source)

    def handle_link(self, name: str) -> None:
        source = self.get_object_source(name)
        if source:
            self.registry().link_remote_node(name, self)
            source.olink_linked(name, self)
            props = source.olink_collect_properties()
            self.emit_write(Protocol.init_message(name, props))
    
    def handle_unlink(self, name: str):
        source = self.get_object_source(name)
        if source:
            self.registry().unlink_remote_node(name, self)

    def handle_set_property(self, name: str, value: Any):
        source = self.get_object_source(name)
        if source:
            source.olink_set_property(name, value)

    def handle_invoke(self, id: int, name: str, args: list[Any]) -> None:
        source = self.get_object_source(name)
        if source:
            value = source.olink_invoke(name, args)
            self.emit_write(Protocol.invoke_reply_message(id, name, value))

    def notify_property_change(self, name: str, value: Any) -> None:
        for node in self.registry().get_remote_nodes(name):
            node.emit_write(Protocol.property_change_message(name, value))

    def notify_signal(self, name: str, args: list[Any]):
        for node in self.registry().get_remote_nodes(name):
            node.emit_write(Protocol.signal_message(name, args))
    

