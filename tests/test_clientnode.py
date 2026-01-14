from olink.client import ClientNode
from olink.mocks import MockSink

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


def test_client_node_invokes_pending_isolation():
    """Two ClientNode instances should have independent invokes_pending dicts"""
    node1 = ClientNode()
    node2 = ClientNode()

    node1.invokes_pending[1] = lambda x: None

    assert 1 not in node2.invokes_pending, "node2 should not see node1's pending invokes"
    assert len(node2.invokes_pending) == 0, "node2 should have empty invokes_pending"


def test_client_node_request_id_isolation():
    """Two ClientNode instances should have independent requestId counters"""
    node1 = ClientNode()
    node2 = ClientNode()

    _ = node1.next_request_id()
    _ = node1.next_request_id()
    _ = node1.next_request_id()

    id2 = node2.next_request_id()
    assert id2 == 1, f"node2 should start at 1, got {id2}"
