from olink.client import ClientNode, ClientRegistry
from olink.mocks.mocksink import MockSink
import pytest

name = "demo.Counter"


@pytest.fixture
def node():  # type: () -> ClientNode
    sink = MockSink(name)
    registry = ClientRegistry()
    registry.add_sink(sink)
    node = ClientNode(registry)
    registry.add_node(name, node)
    assert registry.get_sink(name) == sink
    assert registry.get_node(name) == node
    return node


@pytest.fixture
def registry():  # type: () -> ClientRegistry
    name = "demo.Counter"
    sink = MockSink(name)
    registry = ClientRegistry()
    registry.add_sink(sink)
    return registry


def test_add_sink(node: ClientNode):
    name = "demo.Counter"
    registry = node.registry()
    sink = registry.get_sink(name)
    assert registry.get_sink(name) == sink
    assert registry.get_node(name) == node
    registry.remove_sink(sink)
    assert registry.get_sink(name) == None
    assert registry.get_node(name) == None


def test_remove_sink(node: ClientNode):
    registry = node.registry()
    sink = registry.get_sink(name)
    registry.remove_sink(sink)
    assert registry.get_sink(name) == None
    assert registry.get_node(name) == None


def test_link_node_to_sink(node: ClientNode):
    registry = node.registry()
    assert registry.get_node(name) == node
    node.link_remote(name)
    assert registry.get_node(name) == node


def test_unlink_node_from_sink(node: ClientNode):
    registry = node.registry()
    assert registry.get_node(name) == node
    node.unlink_remote(name)
    assert registry.get_node(name) == None


def test_detach_node_from_all_sinks(node: ClientNode):
    registry = node.registry()
    node.link_remote(name)
    assert registry.get_node(name) == node
    node.detach()
    assert registry.get_node(name) == None
