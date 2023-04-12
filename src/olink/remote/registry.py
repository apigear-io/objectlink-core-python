from olink.core import Name, Base, LogLevel, Protocol
from typing import Any, TYPE_CHECKING
from .types import IObjectSource

if TYPE_CHECKING:
    from .node import RemoteNode


class SourceToNodeEntry:
    def __init__(self, source=None):
        self.source: IObjectSource = source
        self.nodes: set["RemoteNode"] = set()


class RemoteRegistry(Base):
    def __init__(self) -> None:
        super().__init__()
        self._entries: dict[str, SourceToNodeEntry] = {}

    def add_source(self, source: IObjectSource):
        # register a new source in the registry
        name = source.olink_object_name()
        self.emit_log(LogLevel.DEBUG, f"RemoteRegistry.add_object_source: {name}")
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
        for entry in self._entries.values():
            if node in entry.nodes:
                entry.nodes.remove(node)

    def add_node(self, name: str, node: "RemoteNode"):
        # add a node to the named source
        entry = self._entry(name)
        if not node in entry.nodes:
            entry.nodes.add(node)

    def remove_node_from_source(self, name: str, node: "RemoteNode"):
        # remove the given node from the named source
        self._entry(name).nodes.remove(node)

    def _entry(self, name: str) -> SourceToNodeEntry:
        # returns the entry for the given resource part of the name
        resource = Name.resource_from_name(name)
        if not resource in self._entries:
            self.emit_log(LogLevel.DEBUG, f"add new resource: {resource}")
            self._entries[resource] = SourceToNodeEntry()
        return self._entries[resource]

    def _remove_entry(self, name: str) -> None:
        # remove entry from registry
        resource = Name.resource_from_name(name)
        if resource in self._entries:
            del self._entries[resource]
        else:
            self.emit_log(
                LogLevel.DEBUG,
                f"remove resource failed, resource not exists: {resource}",
            )

    def _has_entry(self, name: str) -> SourceToNodeEntry:
        # checks if the registry has an entry for the given name
        resource = Name.resource_from_name(name)
        return resource in self._entries

    def init_entry(self, name: str):
        # init a new entry for the given name
        resource = Name.resource_from_name(name)
        if resource in self._entries:
            self._entries[resource] = SourceToNodeEntry()

    def clear(self):
        self._entries.clear()

    def notify_property_changed(self, name: str, value: Any):
        # notify property change to all named client nodes
        resource = Name.resource_from_name(name)
        for node in self.get_nodes(resource):
            msg = Protocol.property_changed_message(name, value)
            node.emit_write(msg)

    def notify_signal(self, name: str, args: tuple):
        # notify signal to all named client nodes
        resource = Name.resource_from_name(name)
        for node in self.get_nodes(resource):
            msg = Protocol.signal_message(name, args)
            node.emit_write(msg)
