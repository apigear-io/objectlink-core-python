from re import A
from typing import Any, Callable, Optional, Protocol as ProtocolType
from olink.core.types import Base, LogLevel, MsgType, Name
from olink.core.node import BaseNode
from olink.core.protocol import Protocol


class InvokeReplyArg:
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value
    name: str
    value: Any

InvokeReplyFunc = Callable[[InvokeReplyArg], None]

class IObjectSink(ProtocolType):
    def olink_object_name() -> str:
        # return object name
        raise NotImplementedError()

    def olink_on_signal(self, name: str, args: list[Any]) -> None:
        # called on signal message
        raise NotImplementedError()

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        # called on property changed message
        raise NotImplementedError()

    def olink_on_init(self, name: str, props: object, node: "ClientNode"):
        # called on init message
        raise NotImplementedError()

    def olink_on_release(self) -> None:
        # called when sink is released
        raise NotImplementedError()

class SinkToClientEntry:
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
                self.emit_log(LogLevel.DEBUG, f"unlink node failed, not the same node: {resource}")

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
    return _registry

class ClientNode(BaseNode):
    invokes_pending: dict[int, InvokeReplyFunc] = {}
    requestId = 0

    def registry(self) -> ClientRegistry:
        return get_client_registry()

    def detach(self) -> None:
        self.registry().remove_node(self)

    def next_request_id(self) -> int:
        self.requestId += 1
        return self.requestId

    def invoke_remote(self, name: str, args: list[Any], func: Optional[InvokeReplyFunc]) -> None:
        self.emit_log(LogLevel.DEBUG, f"ClientNode.invoke_remote: {name} {args}")
        request_id = self.next_request_id()
        if func:
            self.invokes_pending[request_id] = func
        self.emit_write(Protocol.invoke_message(request_id, name, args))

    def set_remote_property(self, name: str, value: Any) -> None:
        # send remote propertymessage
        self.emit_log(LogLevel.DEBUG, f"ClientNode.set_remote_property: {name} {value}")   
        self.emit_write(Protocol.set_property_message(name, value))

    def link_node(self, name: str):
        # register this node to sink
        self.registry().add_node_to_sink(name, self)

    def unlink_node(self, name: str) -> None:
        # unregister this node from sink
        self.registry().remove_node_from_sink(name, self)

    @staticmethod
    def register_sink(sink: IObjectSink) -> Optional["ClientNode"]:
        # register sink to registry
        return get_client_registry().register_sink(sink)
    
    @staticmethod
    def unregister_sink(sink: IObjectSink) -> None:
        # unregister sink from registry
        return get_client_registry().unregister_sink(sink)

    @staticmethod
    def get_sink(name: str) -> Optional[IObjectSink]:
        return get_client_registry().get_sink(name)

    def link_remote(self, name: str):      
        # register this node from sink and send a link message  
        self.emit_log(LogLevel.DEBUG, f"ClientNode.linkRemote: {name}")
        self.registry().add_node_to_sink(name, self)
        self.emit_write(Protocol.link_message(name))

    def unlink_remote(self, name: str):
        # unlink this node froom sink and send an unlink message
        self.emit_log(LogLevel.DEBUG, f"ClientNode.unlink_remote: {name}")
        self.emit_write(Protocol.unlink_message(name))
        self.registry().remove_node_from_sink(name, self)

    def handle_init(self, name: str, props: object):
        # handle init message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_init: {name}")
        sink = self.get_sink(name)
        if sink:
            sink.olink_on_init(name, props, self)

    def handle_property_change(self, name: str, value: Any) -> None:
        # handle property change message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_property_change: {name}")
        sink =self.get_sink(name)
        if sink:
            sink.olink_on_property_changed(name, value)

    def handle_invoke_reply(self, id: int, name: str, value: Any) -> None:
        # handle invoke reply message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_invoke_reply: {id} {name} {value}")
        if id in self.invokes_pending:
            func = self.invokes_pending[id]
            if func:
                arg = InvokeReplyArg(name, value)
                func(arg)
            del self.invokes_pending[id]
        else:
            self.emit_log(LogLevel.DEBUG, f"no pending invoke: {id} {name}")

    def handle_signal(self, name: str, args: list[Any]) -> None:
        # handle signal message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_signal: {name} {args}")
        sink = self.get_sink(name)
        if sink:
            sink.olink_on_signal(name, args)

    def handle_error(self, msgType: MsgType, id: int, error: str):
        # handle error message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_error: {msgType} {id} {error}")


    
