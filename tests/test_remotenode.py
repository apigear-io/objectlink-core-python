from olink.remotenode import RemoteNode, get_remote_registry
from olink.mocks.mocksource import MockSource

name = "demo.Counter"
source = MockSource(name)
remote = RemoteNode()
remote_registry = get_remote_registry()


def reset():
    source.clear()
    remote_registry.clear()


def test_add_source():
    reset()
    assert len(remote_registry.get_nodes(name)) == 0
    remote.register_source(source)
    assert remote_registry.get_source(name) == source
    assert len(remote_registry.get_nodes(name)) == 0


def test_remove_source():
    reset()
    RemoteNode.register_source(source)
    assert remote_registry.get_source(name) == source
    RemoteNode.unregister_source(source)
    assert remote_registry.get_source(name) == None


def test_link_node_to_source():
    reset()
    RemoteNode.register_source(source)
    assert remote_registry.get_nodes(name) == set()
    remote_registry.add_node_to_source(name, remote)
    assert remote_registry.get_nodes(name) == {remote}


def test_unlink_node_from_source():
    reset()
    RemoteNode.register_source(source)
    remote_registry.add_node_to_source(name, remote)
    assert remote_registry.get_nodes(name) == set([remote])
    remote_registry.remove_node_from_source(name, remote)
    assert remote_registry.get_nodes(name) == set()


def test_detach_node_from_all_sources():
    reset()
    RemoteNode.register_source(source)
    remote_registry.add_node_to_source(name, remote)
    assert remote_registry.get_nodes(name) == set([remote])
    remote.detach()
    assert remote_registry.get_nodes(name) == set()


def test_get_registry():
    reset()
    reg = remote.registry()
    assert reg == remote_registry
