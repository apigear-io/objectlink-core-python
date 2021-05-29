from olink.remotenode import RemoteNode
from olink.mocks.mocksource import MockSource

name = 'demo.Counter'
source = MockSource(name)
remote = RemoteNode()
r = remote.registry()

def reset():
    source.clear()
    r.clear()    

def test_add_source():
    reset()
    assert len(r.get_remote_nodes(name)) == 0
    RemoteNode.add_object_source(source)
    assert r.get_object_source(name) == source
    assert len(r.get_remote_nodes(name)) == 0

def test_remove_source():
    reset()
    RemoteNode.add_object_source(source)
    assert r.get_object_source(name) == source
    RemoteNode.remove_object_source(source)
    assert(r.get_object_source(name) == None)

def test_link_node_to_source():
    reset()
    RemoteNode.add_object_source(source)
    assert r.get_remote_nodes(name) == set()
    r.link_remote_node(name, remote)
    assert r.get_remote_nodes(name) == {remote}

def test_unlink_node_from_source():
    reset()
    RemoteNode.add_object_source(source)
    r.link_remote_node(name, remote)
    assert r.get_remote_nodes(name) == set([remote])    
    r.unlink_remote_node(name, remote)
    assert r.get_remote_nodes(name) == set()    

def test_detach_node_from_all_sources():
    reset()
    RemoteNode.add_object_source(source)
    r.link_remote_node(name, remote)
    assert r.get_remote_nodes(name) == set([remote])    
    remote.detach()
    assert r.get_remote_nodes(name) == set()    
