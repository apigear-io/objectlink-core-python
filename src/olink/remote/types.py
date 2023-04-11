from typing import Any, Protocol as ProtocolType

class IObjectSource(ProtocolType):
    # interface for object sources
    def olink_object_name() -> str:
        # returns the object name
        raise NotImplementedError()

    def olink_invoke(self, name: str, args):
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