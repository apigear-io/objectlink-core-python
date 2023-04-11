from olink.core.protocol import Protocol
from olink.core.types import MsgType, MessageConverter, Name, MessageFormat
from .client import Connection
from asyncio.queues import Queue
from olink.client.node import ClientNode
from olink.client.types import IObjectSink
from unittest import mock
import websockets
import asyncio
import pytest


object_name = 'TestModule.TestObject'
test_host = "localhost"
test_port = 8152
msgConverter = MessageConverter(MessageFormat.JSON)

@pytest.mark.asyncio
async def test_first_test():

    message_queue = asyncio.Queue()
    is_server_done = asyncio.Future()

    async def handle_message(websocket):
        async for message in websocket:
            message_queue.put_nowait(message)

    async def server_setup():
        async with websockets.serve(handle_message, "localhost", 8152):
            await is_server_done

    sink_mock = mock.Mock(spec=IObjectSink)
    sink_mock.olink_object_name = mock.Mock(return_value=object_name)
    node = ClientNode()

    async def client_setup():
        client_connection = Connection(node)
        await client_connection.connect('ws://localhost:8152/ws')

    async def test_scenario():
        node.register_sink(sink_mock)
        node.link_remote(object_name)
        received_link_message = await message_queue.get()
        print(received_link_message)
        is_server_done.set_result(True)


    await asyncio.gather(server_setup(), client_setup(), test_scenario())
    # expected_link_message = msgConverter.to_string(Protocol.link_message(object_name))
    # print(received_link_message)
    # assert received_link_message == expected_link_message



