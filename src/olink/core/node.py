import json
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
    # base node class
    write_func: WriteMessageFunc = None
    converter: MessageConverter = None
    protocol: Protocol = None

    def __init__(self):
        super()
        self.protocol = Protocol(self)
        self.converter = MessageConverter(MessageFormat.JSON)

    def on_log(self, func) -> None:
        # set the log function on both node and protocol
        self.log_func = func
        self.protocol.on_log(func)

    def on_write(self, func: WriteMessageFunc) -> None:
        # set the write function
        self.write_func = func

    def emit_write(self, msg: list[Any]) -> None:
        # emit a message using the write function
        if self.write_func:
            data = self.converter.to_string(msg)
            self.write_func(data)
        else:
            self.emit_log(LogLevel.DEBUG, f"write not set on protocol: {msg}")

    def handle_message(self, data: str) -> None:
        # handle a message and pass it on to the protocol
        try:
            msg = self.converter.from_string(data)
            self.protocol.handle_message(msg)
        except (json.JSONDecodeError, ValueError) as e:
            self.emit_log(LogLevel.ERROR, f"handle_message error: {e}")
