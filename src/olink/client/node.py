from re import A
from typing import Any, Callable, Optional
from olink.core import LogLevel, MsgType, BaseNode, Protocol
from .types import IObjectSink
from .registry import ClientRegistry
import logging


class InvokeReplyArg:
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value


InvokeReplyFunc = Callable[[InvokeReplyArg], None]


class ClientNode(BaseNode):
    def __init__(self, registry: ClientRegistry):
        super().__init__()
        self._invokes_pending: dict[int, InvokeReplyFunc] = {}
        self._requestId: int = 0
        self._registry = registry

    def registry(self) -> ClientRegistry:
        return self._registry

    def detach(self) -> None:
        self.registry().remove_node(self)

    def next_request_id(self) -> int:
        self._requestId += 1
        return self._requestId

    def invoke_remote(
        self, name: str, args: list[Any], func: Optional[InvokeReplyFunc]
    ) -> None:
        self.emit_log(LogLevel.DEBUG, f"ClientNode.invoke_remote: {name} {args}")
        request_id = self.next_request_id()
        if func:
            self._invokes_pending[request_id] = func
        self.emit_write(Protocol.invoke_message(request_id, name, args))

    def set_remote_property(self, name: str, value: Any) -> None:
        # send remote property message
        self.emit_log(LogLevel.DEBUG, f"ClientNode.set_remote_property: {name} {value}")
        self.emit_write(Protocol.set_property_message(name, value))

    def link_node(self, name: str):
        # register this node to sink
        logging.debug(f"ClientNode.linkNode: {name}")
        self.registry().add_node(name, self)

    def unlink_node(self, name: str) -> None:
        # unregister this node from sink
        self.registry().remove_node_from_sink(name, self)

    def link_remote(self, name: str):
        # register this node from sink and send a link message
        self.emit_log(LogLevel.DEBUG, f"ClientNode.linkRemote: {name}")
        self.registry().add_node(name, self)
        self.emit_write(Protocol.link_message(name))

    def unlink_remote(self, name: str):
        # unlink this node from sink and send an unlink message
        self.emit_log(LogLevel.DEBUG, f"ClientNode.unlink_remote: {name}")
        self.emit_write(Protocol.unlink_message(name))
        self.registry().remove_node_from_sink(name, self)

    def handle_init(self, name: str, props: object):
        # handle init message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_init: {name}")
        sink = self.registry().get_sink(name)
        if sink:
            sink.olink_on_init(name, props, self)

    def handle_property_change(self, name: str, value: Any) -> None:
        # handle property change message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_property_change: {name}")
        sink = self.registry().get_sink(name)
        if sink:
            sink.olink_on_property_changed(name, value)

    def handle_invoke_reply(self, id: int, name: str, value: Any) -> None:
        # handle invoke reply message from source
        self.emit_log(
            LogLevel.DEBUG, f"ClientNode.handle_invoke_reply: {id} {name} {value}"
        )
        if id in self._invokes_pending:
            func = self._invokes_pending[id]
            if func:
                arg = InvokeReplyArg(name, value)
                func(arg)
            del self._invokes_pending[id]
        else:
            self.emit_log(LogLevel.DEBUG, f"no pending invoke: {id} {name}")

    def handle_signal(self, name: str, args: list[Any]) -> None:
        # handle signal message from source
        self.emit_log(LogLevel.DEBUG, f"ClientNode.handle_signal: {name} {args}")
        sink = self.registry().get_sink(name)
        if sink:
            sink.olink_on_signal(name, args)

    def handle_error(self, msgType: MsgType, id: int, error: str):
        # handle error message from source
        self.emit_log(
            LogLevel.DEBUG, f"ClientNode.handle_error: {msgType} {id} {error}"
        )
