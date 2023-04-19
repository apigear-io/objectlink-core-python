import asyncio
import pytest
from olink.ws import Connection, run_server
from olink.client import ClientNode, ClientRegistry
import logging

test_host = "localhost"
test_port = 8152
test_url = f"ws://{test_host}:{test_port}"
object_id = "demo.Calc"


async def delay(coro, delay: float):
    await asyncio.sleep(delay)
    await coro


@pytest.mark.asyncio
async def test_client_link():
    logging.info("test_client_link")
    cancel = asyncio.Future()
    server_task = asyncio.create_task(run_server(cancel, test_host, test_port))
    logging.info("server_task %s", server_task)

    async def run_client(cancel: asyncio.Future):
        logging.info("run_client")
        registry = ClientRegistry()
        node = ClientNode(registry)
        conn = Connection(cancel, node)
        node.on_write(conn.send)
        conn.on_recv += node.handle_message
        logging.info("connecting to %s", test_url)
        await conn.connect(test_url, cancel)
        logging.info("connected")
        node.link_node(object_id)
        logging.info("client done")

    client_task = asyncio.create_task(delay(run_client(cancel), 0.5))
    logging.info("client_task %s", client_task)

    done, pending = await asyncio.wait(
        [server_task, client_task], return_when=asyncio.FIRST_COMPLETED
    )
    logging.info("done %s, pending %s", done, pending)
    print(done, pending)
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
