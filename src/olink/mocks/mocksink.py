from olink.core.types import Name
from typing import Any, Optional
from olink.client import ClientNode, IObjectSink, InvokeReplyArg


class MockSink(IObjectSink):
    def __init__(self, name: str):
        self.name = name
        self.events: list[Any] = []
        self.node: Optional[ClientNode] = None
        self.properties: dict[str, Any] = {}

    def invoke(self, name: str, args: list[Any]):
        if self.node:

            def func(arg: InvokeReplyArg):
                self.events.append(
                    {"type": "invoke-reply", "name": arg.name, "value": arg.value}
                )

            self.node.invoke_remote(name, args, func)

    def olink_object_name(self) -> str:
        return self.name

    def olink_on_signal(self, name: str, args: list[Any]) -> None:
        self.events.append({"type": "signal", "name": name, "args": args})

    def olink_on_property_changed(self, name: str, value: Any) -> None:
        path = Name.path_from_name(name)
        self.events.append({"type": "property_change", "name": name, "value": value})
        self.properties[path] = value

    def olink_on_init(self, name: str, props: object, node: "ClientNode"):
        self.events.append({"type": "init", "name": name, "props": props})
        self.node = node
        self.properties = props

    def olink_on_release(self) -> None:
        self.events.append({"type": "release"})
        self.node = None

    def clear(self):
        self.events = []
        self.properties = {}
        self.node = None
