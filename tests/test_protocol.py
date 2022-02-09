from olink.core.protocol import Protocol
from olink.core.types import MsgType

name = 'demo.Calc'
props = {'count':  1}
value = 1
id = 1
args = [1, 2]
msgType = MsgType.INVOKE
error = "error"


def test_messages():
    msg = Protocol.link_message(name)
    assert msg == [MsgType.LINK, name]

    msg = Protocol.unlink_message(name)
    assert msg == [MsgType.UNLINK, name]

    msg = Protocol.init_message(name, props)
    assert msg == [MsgType.INIT, name, props]

    msg = Protocol.set_property_message(name, value)
    assert msg == [MsgType.SET_PROPERTY, name, value]

    msg = Protocol.property_change_message(name, value)
    assert msg == [MsgType.PROPERTY_CHANGE, name, value]

    msg = Protocol.invoke_message(id, name, args)
    assert msg == [MsgType.INVOKE, id, name, args]

    msg = Protocol.invoke_reply_message(id, name, value)
    assert msg == [MsgType.INVOKE_REPLY, id, name, value]

    msg = Protocol.signal_message(name, args)
    assert msg == [MsgType.SIGNAL, name, args]

    msg = Protocol.error_message(msgType, id, error)
    assert msg == [MsgType.ERROR, msgType, id, error]
