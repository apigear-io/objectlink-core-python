from enum import IntEnum
from typing import Any, Callable
from typing import Protocol as ProptocolType
import json


class MsgType(IntEnum):
    LINK = (10,)
    INIT = (11,)
    UNLINK = (12,)
    SET_PROPERTY = (20,)
    PROPERTY_CHANGE = (21,)
    INVOKE = (30,)
    INVOKE_REPLY = (31,)
    SIGNAL = (40,)
    ERROR = (90,)


class MessageFormat(IntEnum):
    JSON = (1,)
    BSON = (2,)
    MSGPACK = (3,)
    CBOR = (4,)


class Name:
    # a name is a resource name (module.Interface) with a path (method, property, signal), joined by a '/'
    # module=demo, interface=Calc, method=add => demo.Calc/add
    @staticmethod
    def resource_from_name(name: str) -> str:
        # return the resource name from a name
        return name.split("/")[0]

    @staticmethod
    def path_from_name(name: str) -> str:
        # return the path from a name
        return name.split("/")[-1]

    @staticmethod
    def has_path(name: str) -> bool:
        # return true if name has a path
        return "/" in name

    @staticmethod
    def create_name(resource: str, path: str) -> str:
        # create a name from a resource and a path
        return f"{resource}/{path}"


class MessageConverter:
    # convert a message from/to a string
    format: MessageFormat = MessageFormat.JSON

    def __init__(self, format: MessageFormat):
        self.format = format

    def from_string(self, message: str) -> list[Any]:
        return json.loads(message)

    def to_string(self, data: list[Any]) -> str:
        return json.dumps(data)


WriteMessageFunc = Callable[[str], None]


class LogLevel:
    DEBUG = (1,)
    INFO = (2,)
    WARNING = (3,)
    ERROR = (4,)


WriteLogFunc = Callable[[LogLevel, str], None]


class ILogger(ProptocolType):
    def log(level: LogLevel, msg: str) -> None:
        raise NotImplementedError()


class Base:
    log_func: WriteLogFunc = None

    def on_log(self, func: WriteLogFunc):
        self.log_func = func

    def emit_log(self, level: LogLevel, msg: str):
        if self.log_func:
            self.log_func(level, msg)
