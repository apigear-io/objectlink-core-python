from typing import Any
from olink.core.types import Name
from .node import RemoteNode
from .types import IObjectSource

class SourceAdapter(IObjectSource):
    node: RemoteNode = None
    object_id: str = None
    def __init__(self, objectId: str, impl) -> None:
        self.object_id = objectId
        self.impl = impl
        RemoteNode.register_source(self)

    def olink_object_name(self) -> str:
        return self.object_id
    
    def olink_invoke(self, name: str) -> Any:
        path = Name.path_from_name(name)
        func = getattr(self.impl, path)
        try:
            result = func(**args)
        except Exception as e:
            print('error: %s' % e)
            result = None
        return result
    
    def olink_set_property(self, name: str, value: Any):
        # set property value on implementation
        path = Name.path_from_name(name)
        setattr(self, self.impl, value)

    def olink_linked(self, name: str, node: "RemoteNode"):
        # called when the source is linked to a client node
        self.node = node

    def olink_collect_properties(self) -> object:
        # collect properties from implementation to send back to client node initially
        return {k: getattr(self.impl, k) for k in ['count']}
