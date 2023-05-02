from olink.clientnode import ClientNode
from olink.mocks.mocksink import MockSink

name = "demo.Counter"
sink = MockSink(name)
client = ClientNode()
r = client.registry()


def test_add_sink():
    ClientNode.register_sink(sink)
    assert r.get_sink(name) == sink
    assert r.get_node(name) == None


def test_remove_sink():
    ClientNode.unregister_sink(sink)
    assert r.get_sink(name) == None


def test_link_node_to_sink():
    assert r.get_node(name) == None
    client.link_remote(name)
    assert r.get_node(name) == client


def test_unlink_node_from_sink():
    assert r.get_node(name) == client
    client.unlink_remote(name)
    assert r.get_node(name) == None


def test_detach_node_from_all_sinks():
    client.link_remote(name)
    assert r.get_node(name) == client
    client.detach()
    assert r.get_node(name) == None
