from olink.core.types import Name
from typing import Any
from olink.remote import IObjectSource, RemoteNode


class MockSource(IObjectSource):
    def __init__(self, name: str):
        self.name = name
        self.events: list[Any] = []
        self.properties: dict[str, Any] = {}
        self.node: RemoteNode = None

    def set_property(self, name: str, value: Any):
        path = Name.path_from_name(name)
        if self.properties.get(path) != value:
            self.properties[path] = value
            self.get_node().notify_property_changed(name, value)

    def notify_signal(self, name: str, args: list[Any]):
        self.get_node().notify_signal(name, args)

    def olink_object_name(self) -> str:
        return self.name

    def olink_invoke(self, name: str, args: list[Any]):
        self.events.append({"type": "invoke", "name": name, "args": args})
        return name

    def olink_set_property(self, name: str, value: Any):
        self.events.append({"type": "set_property", "name": name, "value": value})
        self.set_property(name, value)

    def olink_linked(self, name: str, node: RemoteNode):
        self.node = node
        self.events.append({"type": "linked", "name": name})

    def olink_collect_properties(self) -> object:
        return self.properties

    def get_node(self) -> RemoteNode:
        if not self.node:
            raise Exception("Node not set")
        return self.node

    def clear(self):
        self.events = []
        self.properties = {}
        self.node = None
