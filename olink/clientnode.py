from re import A
from typing import Any, Callable, Optional, Protocol as ProtocolType
from olink.core.types import Base, LogLevel, MsgType, Name
from olink.core.node import BaseNode
from olink.core.protocol import Protocol


class InvokeReplyArg(ProtocolType):
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value
    name: str
    value: Any

InvokeReplyFunc = Callable[[InvokeReplyArg], None]

class IObjectSink(ProtocolType):
    def olink_object_name() -> str:
        raise NotImplementedError()

    def olink_on_signal(self, name: str, args: list[Any]) -> None:
        raise NotImplementedError()

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        raise NotImplementedError()

    def olink_on_init(self, name: str, props: object, node: "ClientNode"):
        raise NotImplementedError()

    def olink_on_release(self) -> None:
        raise NotImplementedError()

class SinkToClientEntry:
    sink: IObjectSink = None
    node: "ClientNode" = None


class ClientRegistry(Base):
    entries: dict[str, SinkToClientEntry] = {}
    def attach_client_node(self, node: "ClientNode"):
        pass

    def detach_client_node(self, node: "ClientNode"):
        for entry in self.entries.values():
            if entry.node is node:
                entry.node = None

    def link_client_node(self, name: str, node: "ClientNode"):
        resource = Name.resource_from_name(name)
        self.init_entry(resource)
        if not self.entries[resource].node:
            self.entries[resource].node = node
        else:
            self.emit_log(LogLevel.DEBUG, f"link node failed, sink has already a node: {resource}")

    def unlink_client_node(self, name: str, node: "ClientNode"):
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            if self.entries[resource].node is node:
                self.entries[resource].node = None
            else:
                self.emit_log(LogLevel.DEBUG, f"unlink node failed, not the same node: {resource}")

    def add_object_sink(self, sink: IObjectSink) -> "ClientNode":
        resource = Name.resource_from_name(sink.olink_object_name())
        self.init_entry(resource)
        if not self.entries[resource].sink:
            self.entries[resource].sink = sink
        else:
            self.emit_log(LogLevel.DEBUG, f"add object sink failed: sink already added: {resource}")
        return self.entries[resource].node

    def remove_object_sink(self, sink: IObjectSink):
        resource = Name.resource_from_name(sink.olink_object_name())
        if self.entries[resource].sink:
            del self.entries[resource]
        else:
            self.emit_log(LogLevel.DEBUG, f"remove object sink failed: no sink to remove {resource}")
        
    def get_object_sink(self, name: str) -> Optional[IObjectSink]:
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            sink = self.entries[resource].sink
            if not sink:
                self.emit_log(LogLevel.DEBUG, f"no sink attached {resource}")
            return sink
        else:
            self.emit_log(LogLevel.DEBUG, f"no resource: {resource}")
        return None

    def get_client_node(self, name: str) -> Optional["ClientNode"]:
        resource = Name.resource_from_name(name)
        if resource in self.entries:
            node = self.entries[resource].node
            if not node:
                self.emit_log(LogLevel.DEBUG, f"no node attached {resource}")
            return node
        else:
            self.emit_log(LogLevel.DEBUG, f"no resource: {resource}")
        return None

    def entry(self, name: str) -> SinkToClientEntry:
        resource = Name.resource_from_name(name)
        return self.entries[resource]

    def has_entry(self, name: str) -> bool:
        resource = Name.resource_from_name(name)
        return resource in self.entries

    def init_entry(self, name: str):
        resource = Name.resource_from_name(name)
        if resource not in self.entries:
            self.entries[resource] = SinkToClientEntry()

    

_registry = ClientRegistry()


class ClientNode(BaseNode):
    invokes_pending: dict[int, InvokeReplyFunc] = {}
    requestId = 0

    def __init__(self):
        super().__init__()
        self.registry().attach_client_node(self)

    def registry(self) -> ClientRegistry:
        return _registry

    def detach(self) -> None:
        self.registry().detach_client_node(self)

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
        self.emit_log(LogLevel.DEBUG, f"ClientNode.set_remote_property: {name} {value}")   
        self.emit_write(Protocol.set_property_message(name, value))

    def link_node(self, name: str):
        self.registry().link_client_node(name, self)

    def unlink_node(self, name: str) -> None:
        self.registry().unlink_client_node(name, self)

    @staticmethod
    def add_object_sink(sink: IObjectSink) -> Optional["ClientNode"]:
        return _registry.add_object_sink(sink)
    
    @staticmethod
    def remove_object_sink(sink: IObjectSink) -> None:
        return _registry.remove_object_sink(sink)

    def get_object_sink(self, name: str) -> Optional[IObjectSink]:
        return self.registry().get_object_sink(name)

    def link_remote(self, name: str):        
        self.emit_log(LogLevel.DEBUG, f"ClientNode.linkRemote: {name}")
        self.registry().link_client_node(name, self)
        self.emit_write(Protocol.link_message(name))

    def unlink_remote(self, name: str):
        self.emit_log(LogLevel.DEBUG, f"ClientNode.unlink_remote: {name}")
        self.emit_write(Protocol.unlink_message(name))
        self.registry().unlink_client_node(name, self)

    def handle_init(self, name: str, props: object):
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_init: {name}")
        sink = self.get_object_sink(name)
        if sink:
            sink.olink_on_init(name, props, self)

    def handle_property_change(self, name: str, value: Any) -> None:
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_property_change: {name}")
        sink =self.get_object_sink(name)
        if sink:
            sink.olink_on_property_changed(name, value)

    def handle_invoke_reply(self, id: int, name: str, value: Any) -> None:
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
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_signal: {name} {args}")
        sink = self.get_object_sink(name)
        if sink:
            sink.olink_on_signal(name, args)

    def handle_error(self, msgType: MsgType, id: int, error: str):
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_error: {msgType} {id} {error}")


    
