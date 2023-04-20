from .types import IObjectSink
from olink.core import Name, Base, LogLevel
from typing import Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .node import ClientNode


class SinkToClientEntry:
    def __init__(self, sink=None):
        self.sink: IObjectSink = sink
        self.node: "ClientNode" = None


class ClientRegistry(Base):
    def __init__(self) -> None:
        super().__init__()
        logging.debug("ClientRegistry.__init__")
        self.entries: dict[str, SinkToClientEntry] = {}

    def remove_node(self, node: "ClientNode"):
        logging.debug("ClientRegistry.removeNode")
        # remove node from all sinks
        for entry in self.entries.values():
            if entry.node is node:
                entry.node = None

    def add_node(self, name: str, node: "ClientNode"):
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

    def add_sink(self, sink: IObjectSink) -> "ClientNode":
        # register sink using object name
        name = sink.olink_object_name()
        entry = self._entry(name)
        entry.sink = sink

    def remove_sink(self, sink: IObjectSink):
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
