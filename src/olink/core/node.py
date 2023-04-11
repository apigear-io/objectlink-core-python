from typing import Any
from olink.core.protocol import IProtocolListener, Protocol
from olink.core.types import Base, LogLevel, MessageConverter, MessageFormat, WriteMessageFunc


class BaseNode(Base, IProtocolListener):
    # base node class
    write_func: WriteMessageFunc = None
    converter: MessageConverter = None
    protocol: Protocol = None

    def __init__(self):
        super()
        self.protocol = Protocol(self)
        self.converter = MessageConverter(MessageFormat.JSON)

    def on_write(self, func: WriteMessageFunc) -> None:
        # set the write function
        self.write_func = func

    def emit_write(self, msg) -> None:
        # emit a message using the write function
        if self.write_func:
            data = self.converter.to_string(msg)
            self.write_func(data)
        else:
            self.emit_log(LogLevel.DEBUG, f"write not set on protocol: {msg}")

    def handle_message(self, data: str) -> None:
        # handle a message and pass is on to the protocol
        msg = self.converter.from_string(data)
        self.protocol.handle_message(msg)
