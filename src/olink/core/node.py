from typing import Any
from olink.core.protocol import IProtocolListener, Protocol
from olink.core.types import (
    Base,
    LogLevel,
    MessageConverter,
    MessageFormat,
    WriteMessageFunc,
)


class BaseNode(Base, IProtocolListener):
    def __init__(self):
        super().__init__()
        self._protocol = Protocol(self)
        self._converter = MessageConverter(MessageFormat.JSON)
        self._write_func: WriteMessageFunc = None

    def on_write(self, func: WriteMessageFunc) -> None:
        # set the write function
        self._write_func = func

    def emit_write(self, msg: list[Any]) -> None:
        # emit a message using the write function
        if self._write_func:
            data = self._converter.to_string(msg)
            self._write_func(data)
        else:
            self.emit_log(LogLevel.DEBUG, f"write not set on protocol: {msg}")

    def handle_message(self, data: str) -> None:
        # handle a message and pass is on to the protocol
        msg = self._converter.from_string(data)
        self._protocol.handle_message(msg)
