from typing import Any, Protocol as ProtocolType
from .types import Base, LogLevel, MsgType


class IProtocolListener(ProtocolType):
    # interface for protocol listeners
    def handle_link(self, name: str) -> None:
        # called when a link is created
        raise NotImplementedError()

    def handle_unlink(self, name: str) -> None:
        # called when a link is released
        raise NotImplementedError()

    def handle_init(self, name: str, props: object) -> None:
        # called when a node is initialized
        raise NotImplementedError()

    def handle_set_property(self, name: str, value: Any) -> None:
        # called when a property is set
        raise NotImplementedError()

    def handle_property_change(self, name: str, value: Any) -> None:
        # called when a property is changed
        raise NotImplementedError()

    def handle_invoke(self, id: int, name: str, args: list[Any]) -> None:
        # called when a node invokes a method
        raise NotImplementedError()

    def handle_invoke_reply(self, id: int, name: str, value: Any) -> None:
        # called when a node replies to an invoke
        raise NotImplementedError()

    def handle_signal(self, name: str, args: Any) -> None:
        # called when a signal is emitted
        raise NotImplementedError()

    def handle_error(self, msgType: int, id: int, error: str) -> None:
        # called when an error occurs
        raise NotImplementedError()


class Protocol(Base):
    listener: IProtocolListener = None

    def __init__(self, listener: IProtocolListener):
        super()
        self.listener = listener

    @staticmethod
    def link_message(name: str) -> list[Any]:
        """links remote object"""
        return [MsgType.LINK, name]

    @staticmethod
    def init_message(name: str, props: object) -> list[Any]:
        return [MsgType.INIT, name, props]

    @staticmethod
    def unlink_message(name: str) -> list[Any]:
        """unlinks remote object"""
        return [MsgType.UNLINK, name]

    @staticmethod
    def set_property_message(name: str, value: Any) -> list[Any]:
        """set property on remote object"""
        return [MsgType.SET_PROPERTY, name, value]

    @staticmethod
    def property_change_message(name: str, value: Any) -> list[Any]:
        """signal property change to the client linked to the remote objects"""
        return [MsgType.PROPERTY_CHANGE, name, value]

    @staticmethod
    def invoke_message(id: int, name: str, args: list[Any]) -> list[Any]:
        """invoke an operation on a remote object"""
        return [MsgType.INVOKE, id, name, args]

    @staticmethod
    def invoke_reply_message(id: int, name: str, value: Any) -> list[Any]:
        """reply on an  invoke message"""
        return [MsgType.INVOKE_REPLY, id, name, value]

    @staticmethod
    def signal_message(name: str, args: list[Any]) -> list[Any]:
        return [MsgType.SIGNAL, name, args]

    @staticmethod
    def error_message(msgType: MsgType, id: int, error: str) -> list[Any]:
        return [MsgType.ERROR, msgType, id, error]

    # Minimum required element counts per message type (use >= for forward-compat)
    _MIN_LENGTHS = {
        MsgType.LINK: 2,
        MsgType.UNLINK: 2,
        MsgType.INIT: 3,
        MsgType.SET_PROPERTY: 3,
        MsgType.PROPERTY_CHANGE: 3,
        MsgType.SIGNAL: 3,
        MsgType.INVOKE: 4,
        MsgType.INVOKE_REPLY: 4,
        MsgType.ERROR: 4,
    }

    def handle_message(self, msg: list[Any]) -> bool:
        if not self.listener:
            self.emit_log(LogLevel.DEBUG, "no listener installed")
            return False
        if not isinstance(msg, list) or len(msg) < 1:
            self.emit_log(LogLevel.ERROR, "invalid message: expected non-empty list")
            return False
        msgType = msg[0]
        min_len = self._MIN_LENGTHS.get(msgType)
        if min_len is not None and len(msg) < min_len:
            self.emit_log(
                LogLevel.ERROR,
                f"malformed message: type {msgType} requires"
                f" at least {min_len} elements, got {len(msg)}",
            )
            return False
        if msgType == MsgType.LINK:
            self.listener.handle_link(msg[1])
        elif msgType == MsgType.INIT:
            self.listener.handle_init(msg[1], msg[2])
        elif msgType == MsgType.UNLINK:
            self.listener.handle_unlink(msg[1])
        elif msgType == MsgType.SET_PROPERTY:
            self.listener.handle_set_property(msg[1], msg[2])
        elif msgType == MsgType.PROPERTY_CHANGE:
            self.listener.handle_property_change(msg[1], msg[2])
        elif msgType == MsgType.INVOKE:
            self.listener.handle_invoke(msg[1], msg[2], msg[3])
        elif msgType == MsgType.INVOKE_REPLY:
            self.listener.handle_invoke_reply(msg[1], msg[2], msg[3])
        elif msgType == MsgType.SIGNAL:
            self.listener.handle_signal(msg[1], msg[2])
        elif msgType == MsgType.ERROR:
            self.listener.handle_error(msg[1], msg[2], msg[3])
        else:
            self.emit_log(LogLevel.DEBUG, f"not supported message type: {msgType}")
            return False
        return True
