import asyncio
import pytest
from olink.ws import Connection, Server
from olink.client import ClientNode, ClientRegistry
import logging

test_host = "localhost"
test_port = 8152
test_url = f"ws://{test_host}:{test_port}"
object_id = "demo.Calc"


async def delay(coro, delay: float):
    await asyncio.sleep(delay)
    await coro


async def delay_cancel(cancel: asyncio.Future, delay: float):
    await asyncio.sleep(delay)
    if not cancel.is_set():
        cancel.set()


@pytest.mark.asyncio
async def test_client_link():
    logging.info("test_client_link")
    cancel = asyncio.Event()
    server = Server(cancel)
    server_task = asyncio.create_task(server.serve(test_host, test_port), name="server")

    client_registry = ClientRegistry()
    client_node = ClientNode(client_registry)
    conn = Connection(cancel)
    client_node.on_write(conn.send)
    conn.on("message", client_node.handle_message)

    async def run_client(conn: Connection, cancel: asyncio.Event):
        logging.info("run_client")
        logging.info("connecting to %s", test_url)
        await conn.connect(test_url)
        await cancel.wait()

    await asyncio.sleep(1)
    client_task = asyncio.create_task(run_client(conn, cancel), name="client")
    await delay_cancel(cancel, 0)
    await server.cancel()
    await conn.cancel()
    await asyncio.wait([server_task, client_task])
