from olink.core.protocol import Protocol
from olink.core.types import Base, LogLevel, Name
from olink.core.node import BaseNode

from typing import Any, Protocol as ProtocolType


class IObjectSource(ProtocolType):
    # interface for object sources
    def olink_object_name() -> str:
        # returns the object name
        raise NotImplementedError()

    def olink_invoke(self, name: str, args: list[Any]):
        # called on incoming invoke message
        # returns resulting value
        raise NotImplementedError()

    def olink_set_property(self, name: str, value: Any):
        # called on incoming set property message
        raise NotImplementedError()

    def olink_linked(self, name: str, node: "RemoteNode"):
        # called when a remote node is linked to this node
        raise NotImplementedError()

    def olink_collect_properties(self) -> object:
        # returns a dictionary of all properties
        raise NotImplementedError()


class SourceToNodeEntry:
    # entry in the remote registry
    source: IObjectSource = None
    nodes: set["RemoteNode"] = set()

    def __init__(self, source=None):
        self.source = source
        self.nodes = set()


class RemoteRegistry(Base):
    # registry of remote sources
    # links sources to nodes
    entries: dict[str, SourceToNodeEntry] = {}

    def add_source(self, source: IObjectSource):
        # add a source to registry by object name
        name = source.olink_object_name()
        self.emit_log(LogLevel.DEBUG,
                      f"RemoteRegistry.add_object_source: {name}")
        self._entry(name).source = source

    def remove_source(self, source: IObjectSource):
        # remove the given source from the registry
        name = source.olink_object_name()
        self._remove_entry(name)

    def get_source(self, name: str):
        # return the source for the given name
        return self._entry(name).source

    def get_nodes(self, name: str):
        # return nodes attached to the named source
        return self._entry(name).nodes

    def remove_node(self, node: "RemoteNode"):
        # remove the given node from the registry
        self.emit_log(LogLevel.DEBUG, "RemoteRegistry.detach_remote_node")
        for entry in self.entries.values():
            if node in entry.nodes:
                entry.nodes.remove(node)

    def add_node_to_source(self, name: str, node: "RemoteNode"):
        # add a node to the named source
        self._entry(name).nodes.add(node)

    def remove_node_from_source(self, name: str, node: "RemoteNode"):
        # remove the given node from the named source
        self._entry(name).nodes.remove(node)

    def _entry(self, name: str) -> SourceToNodeEntry:
        # returns the entry for the given resource part of the name
        resource = Name.resource_from_name(name)
        if not resource in self.entries:
            self.emit_log(LogLevel.DEBUG, f"add new resource: {resource}")
            self.entries[resource] = SourceToNodeEntry()
        return self.entries[resource]

    def _remove_entry(self, name: str) -> None:
        # remove entry from registry
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            del self.entries[resource]
        else:
            self.emit_log(
                LogLevel.DEBUG, f'remove resource failed, resource not exists: {resource}')

    def _has_entry(self, name: str) -> SourceToNodeEntry:
        # checks if the registry has an entry for the given name
        resource = Name.resource_from_name(name)
        return resource in self.entries

    def init_entry(self, name: str):
        # init a new entry for the given name
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            self.entries[resource] = SourceToNodeEntry()

    def clear(self):
        self.entries = {}


_registry = RemoteRegistry()


def get_remote_registry() -> RemoteRegistry:
    # returns the remote registry
    return _registry


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
