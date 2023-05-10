from olink.core import Base, LogLevel, Name
from .source import IObjectSource

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
                LogLevel.DEBUG,
                f"remove resource failed, resource not exists: {resource}",
            )

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
