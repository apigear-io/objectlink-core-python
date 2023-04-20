from olink.client import ClientNode, ClientRegistry
from olink.remote import RemoteNode, RemoteRegistry
from olink.mocks.mocksink import MockSink
from olink.mocks.mocksource import MockSource
from typing import Tuple
import pytest

name = "demo.Calc"
propName = "demo.Calc/total"
propValue = 1
invokeName = "demo.Calc/add"
invokeArgs = [1]
sigName = "demo.Calc/down"
sigArgs = [5]
# remote_registry = RemoteRegistry()
# client_registry = ClientRegistry()
# client = ClientNode(client_registry)
# remote = RemoteNode(remote_registry)
# client.on_log(lambda level, msg: print(msg))
# remote.on_log(lambda level, msg: print(msg))
# client.on_write(lambda msg: remote.handle_message(msg))
# remote.on_write(lambda msg: client.handle_message(msg))
# sink = MockSink(name)
# source = MockSource(name)
# remote_registry.add_source(source)


@pytest.fixture
def client():
    registry = ClientRegistry()
    client = ClientNode(registry)
    client.on_log(lambda level, msg: print(msg))
    sink = MockSink(name)
    registry.add_sink(sink)
    registry.add_node(name, client)
    assert registry.get_sink(name) == sink
    assert registry.get_node(name) == client
    return client


@pytest.fixture
def remote():
    registry = RemoteRegistry()
    remote = RemoteNode(registry)
    remote.on_log(lambda level, msg: print(msg))
    source = MockSource(name)
    registry.add_source(source)
    registry.add_node(name, remote)
    assert registry.get_source(name) == source
    assert len(registry.get_nodes(name)) == 1
    assert remote in registry.get_nodes(name)
    return remote


@pytest.fixture
def conn(client, remote):
    client.on_write(lambda msg: remote.handle_message(msg))
    remote.on_write(lambda msg: client.handle_message(msg))
    print("conn: remote node", hash(remote))
    return client, remote


def test_client_link(conn: Tuple[ClientNode, RemoteNode]):
    client, _ = conn
    client.detach()
    registry = client.registry()
    sink = registry.get_sink(name)  # type: MockSink
    assert registry.get_node(name) == None
    client.link_remote(name)
    assert registry.get_node(name) == client
    assert len(sink.events) == 1
    assert sink.events[0] == {"type": "init", "name": name, "props": {}}


def test_client_set_property(conn: Tuple[ClientNode, RemoteNode]):
    client, _ = conn
    registry = client.registry()
    sink = registry.get_sink(name)  # type: MockSink
    client.link_remote(name)
    assert len(sink.events) == 1
    client.set_remote_property(propName, propValue)
    assert len(sink.events) == 2
    assert sink.events[1] == {
        "type": "property_change",
        "name": propName,
        "value": propValue,
    }


def test_client_invoke(conn: Tuple[ClientNode, RemoteNode]):
    client, _ = conn
    registry = client.registry()
    sink = registry.get_sink(name)  # type: MockSink
    client.link_remote(name)
    assert len(sink.events) == 1
    sink.invoke(invokeName, invokeArgs)
    assert len(sink.events) == 2
    assert sink.events[1] == {
        "type": "invoke-reply",
        "name": invokeName,
        "value": invokeName,
    }


def test_remote_signal(conn: Tuple[ClientNode, RemoteNode]):
    client, remote = conn
    client.link_remote(name)
    client_registry = client.registry()
    sink = client_registry.get_sink(name)  # type: MockSink
    assert len(sink.events) == 1
    remote_registry = remote.registry()
    source = remote_registry.get_source(name)  # type: MockSource
    source.notify_signal(sigName, sigArgs)
    assert len(sink.events) == 2
    assert sink.events[1] == {"type": "signal", "name": sigName, "args": sigArgs}


def test_remote_set_property(conn: Tuple[ClientNode, RemoteNode]):
    client, remote = conn
    client_registry = client.registry()
    sink = client_registry.get_sink(name)  # type: MockSink
    remote_registry = remote.registry()
    source = remote_registry.get_source(name)  # type: MockSource
    client.link_remote(name)
    assert len(sink.events) == 1
    source.set_property(propName, propValue)
    assert len(sink.events) == 2
    assert sink.events[1] == {
        "type": "property_change",
        "name": propName,
        "value": propValue,
    }
