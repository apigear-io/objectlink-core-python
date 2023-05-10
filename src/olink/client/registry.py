from typing import Optional
from olink.core import LogLevel, Base, Name
from .sink import IObjectSink


class SinkToClientEntry:
    # entry in the client registry
    sink: IObjectSink = None
    node: "ClientNode" = None

    def __init__(self, sink=None):
        self.sink = sink
        self.node = None


class ClientRegistry(Base):
    # client side registry to link sinks to nodes
    entries: dict[str, SinkToClientEntry] = {}

    def remove_node(self, node: "ClientNode"):
        # remove node from all sinks
        for entry in self.entries.values():
            if entry.node is node:
                entry.node = None

    def add_node_to_sink(self, name: str, node: "ClientNode"):
        # add not to named sink
        self._entry(name).node = node

    def remove_node_from_sink(self, name: str, node: "ClientNode"):
        # remove node from named sink
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            if self.entries[resource].node is node:
                self.entries[resource].node = None
            else:
                self.emit_log(
                    LogLevel.DEBUG, f"unlink node failed, not the same node: {resource}"
                )

    def register_sink(self, sink: IObjectSink) -> "ClientNode":
        # register sink using object name
        name = sink.olink_object_name()
        entry = self._entry(name)
        entry.sink = sink
        return entry.node

    def unregister_sink(self, sink: IObjectSink):
        # unregister sink using object name
        name = sink.olink_object_name()
        self._remove_entry(name)

    def get_sink(self, name: str) -> Optional[IObjectSink]:
        # get sink using name
        return self._entry(name).sink

    def get_node(self, name: str) -> Optional["ClientNode"]:
        # get node using name
        return self._entry(name).node

    def _entry(self, name: str) -> SinkToClientEntry:
        # get an entry by name
        resource = Name.resource_from_name(name)
        if not resource in self.entries:
            self.emit_log(LogLevel.DEBUG, f"add new resource: {resource}")
            self.entries[resource] = SinkToClientEntry()
        return self.entries[resource]

    def _remove_entry(self, name: str) -> None:
        # remove an entry by name
        resource = Name.resource_from_name(name)
        del self.entries[resource]


# global client registry
_registry = ClientRegistry()


def get_client_registry() -> ClientRegistry:
    # get global client registry
    return _registry


