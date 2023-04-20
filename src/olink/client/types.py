from typing import Any, Protocol as ProtocolType

class IObjectSink(ProtocolType):
    # interface for object sinks
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