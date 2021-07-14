from olink.core.types import Name
from typing import Any
from olink.remotenode import IObjectSource, RemoteNode

class MockSource(IObjectSource):
    name: str
    events: list[Any] = []
    properties: dict[str, Any] = {}
    node: RemoteNode = None

    def __init__(self, name: str):
        self.name = name
        RemoteNode.add_object_source(self)

    def set_property(self, name: str, value: Any):
        if self.node:
            self.node.notify_property_change(name, value)

    def notify_signal(self, name: str, args: list[Any]):
        if self.node:
            self.node.notify_signal(name, args)

    def olink_object_name(self) -> str:
        return self.name

    def olink_invoke(self, name: str, args: list[Any]):
        self.events.append({ 'type': 'invole', 'name': name, 'args': args })
        return name

    def olink_set_property(self, name: str, value: Any):
        path = Name.path_from_name(name)
        self.events.append({'type': 'set_property', 'name': name, 'value': value})
        if not path in self.properties:
            # assign new value
            self.properties[path] = value
            if self.node:
                self.node.notify_property_change(name, value)
        else:
            # update existing value
            if not self.properties[path] == value:
                self.properties[path] = value
                if self.node:
                    self.node.notify_property_change(name, value)
    
    def olink_linked(self, name: str, node: RemoteNode):
        self.events.append({'type': 'linked', 'name': name})
        self.node = node

    def olink_collect_properties(self) -> object:
        return self.properties

    def clear(self):
        self.events = []
        self.properties = {}
        self.node = None