import pytest
import websockets as ws
import asyncio

test_host = "localhost"
test_port = 8152


async def setup_server(
    done: asyncio.Future, queue: asyncio.Queue, host: str, port: int
):
    async def handler(socket: ws.WebSocketServerProtocol):
        async for msg in socket:
            await queue.put(msg)
        done.set_result(True)

    await ws.serve(handler, host, port)
    await done
    await ws.close()


@pytest.mark.asyncio
async def test_client_link():
    queue = asyncio.Queue()
    await setup_server(queue, test_host, test_port)
