from typing import Any
from typing import Protocol as ProptocolType
from .types import Base, LogLevel, MsgType

class IProtocolListener(ProptocolType):
    def handle_link(self, name: str) -> None:
        raise NotImplementedError()

    def handle_unlink(self, name: str) -> None:
        raise NotImplementedError()

    def handle_init(self, name: str, props: object) -> None:
        raise NotImplementedError()

    def handle_set_property(self, name: str, value: Any) -> None:
        raise NotImplementedError()

    def handle_property_change(self, name: str, value: Any) -> None:
        raise NotImplementedError()

    def handle_invoke(self, id: int, name: str, args: list[Any]) -> None:
        raise NotImplementedError()

    def handle_invoke_reply(self, id: int, name: str, value: Any) -> None:
        raise NotImplementedError()

    def handle_signal(self, name: str, args: Any) -> None:
        raise NotImplementedError()

    def handle_error(self, msgType: int, id: int, error: str) -> None:
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

    def handle_message(self, msg: list[Any]) -> bool:
        if not self.listener:
            self.emit_log(LogLevel.DEBUG, "no listener installed")
            return False
        msgType = msg[0]
        if msgType == MsgType.LINK:
            _, name = msg
            self.listener.handle_link(name)
        elif msgType == MsgType.INIT:
            _, name, props = msg
            self.listener.handle_init(name, props)
        elif msgType == MsgType.UNLINK:
            _, name = msg
            self.listener.handle_unlink(name)
        elif msgType == MsgType.SET_PROPERTY:
            _, name, value = msg
            self.listener.handle_set_property(name, value)
        elif msgType == MsgType.PROPERTY_CHANGE:
            _, name, value = msg
            self.listener.handle_property_change(name, value)
        elif msgType == MsgType.INVOKE:
            _, id, name, args = msg
            self.listener.handle_invoke(id, name, args)
        elif msgType == MsgType.INVOKE_REPLY:
            _, id, name, value = msg
            self.listener.handle_invoke_reply(id, name, value)
        elif msgType == MsgType.SIGNAL:
            _, name, args = msg
            self.listener.handle_signal(name, args)
        elif msgType == MsgType.ERROR:
            _, msgType, id, error = msg
            self.listener.handle_error(msgType, id, error)
        else:
            self.emit_log(LogLevel.DEBUG, f"not supported message type: {msgType}")
            return False
        return True


    

    


