from olink.remote import RemoteNode, RemoteRegistry
from olink.mocks.mocksource import MockSource

name = "demo.Counter"
source = MockSource(name)
registry = RemoteRegistry()
remote = RemoteNode(registry)


def reset():
    source.clear()
    registry.clear()


def test_add_source():
    reset()
    assert len(registry.get_nodes(name)) == 0
    registry.add_source(source)
    assert registry.get_source(name) == source
    assert len(registry.get_nodes(name)) == 0


def test_remove_source():
    reset()
    registry.add_source(source)
    assert registry.get_source(name) == source
    registry.remove_source(source)
    assert registry.get_source(name) == None


def test_link_node_to_source():
    reset()
    registry.add_source(source)
    assert registry.get_nodes(name) == set()
    registry.add_node(name, remote)
    assert registry.get_nodes(name) == {remote}


def test_unlink_node_from_source():
    reset()
    registry.add_source(source)
    registry.add_node(name, remote)
    assert remote in registry.get_nodes(name)
    registry.remove_node_from_source(name, remote)
    assert registry.get_nodes(name) == set()


def test_detach_node_from_all_sources():
    reset()
    registry.add_source(source)
    registry.add_node(name, remote)
    assert registry.get_nodes(name) == set([remote])
    remote.detach()
    assert registry.get_nodes(name) == set()


def test_get_registry():
    reset()
    reg = remote.registry()
    assert reg == registry
