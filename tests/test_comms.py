from olink.clientnode import ClientNode
from olink.remotenode import RemoteNode
from olink.mocks.mocksink import MockSink
from olink.mocks.mocksource import MockSource

name = 'demo.Calc'
propName = 'demo.Calc/total'
propValue = 1
invokeName = 'demo.Calc/add'
invokeArgs = [1]
sigName = 'demo.Calc/down'
sigArgs = [5]
client = ClientNode()
remote = RemoteNode()
client.on_log(lambda level, msg: print(msg))
remote.on_log(lambda level, msg: print(msg))
client.on_write(lambda msg: remote.handle_message(msg))
remote.on_write(lambda msg: client.handle_message(msg))
sink = MockSink(name)
source = MockSource(name)

def reset():
    sink.clear()
    source.clear()

def test_client_link():
    client.detach()
    assert client.registry().get_client_node(name) == None
    client.link_remote(name)
    assert client.registry().get_client_node(name) == client
    assert len(sink.events) == 1
    assert sink.events[0] == { 'type': 'init', 'name': name, 'props': {}}


def test_client_set_property():
    reset()
    client.link_remote(name)
    assert len(sink.events) == 1
    client.set_remote_property(propName, propValue)
    assert len(sink.events) == 2
    assert sink.events[1] == { 'type': 'property_change', 'name': propName, 'value': propValue }

def test_client_invoke():
    reset()
    client.link_remote(name)
    assert len(sink.events) == 1
    sink.invoke(invokeName, invokeArgs)
    assert len(sink.events) == 2
    assert sink.events[1] == { 'type': 'invoke-reply', 'name': invokeName, 'value': invokeName }

def test_remote_signal():
    reset()
    client.link_remote(name)
    assert len(sink.events) == 1
    source.notify_signal(sigName, sigArgs)
    assert len(sink.events) == 2
    assert sink.events[1] == { 'type': 'signal', 'name': sigName, 'args': sigArgs }


def test_remote_set_property():
    reset()
    client.link_remote(name)
    assert len(sink.events) == 1
    source.set_property(propName, propValue)
    assert len(sink.events) == 2
    assert sink.events[1] == { 'type': 'property_change', 'name': propName, 'value': propValue }
