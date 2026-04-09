# ObjectLink Core Python

[![CI](https://github.com/apigear-io/objectlink-core-python/actions/workflows/ci.yml/badge.svg)](https://github.com/apigear-io/objectlink-core-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/olink-core)](https://pypi.org/project/olink-core/)
[![Python](https://img.shields.io/pypi/pyversions/olink-core)](https://pypi.org/project/olink-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A transport-agnostic protocol library for remote object communication in Python.
ObjectLink enables linking local objects to remote counterparts, supporting property synchronization, method invocation with request-reply semantics, and signal broadcasting -- all over a lightweight JSON wire protocol.

Part of the [ApiGear](https://apigear.io) ecosystem.

## Features

- **Property synchronization** -- get and set properties on remote objects with automatic change notifications
- **Method invocation** -- call remote methods with arguments and receive replies via callbacks
- **Signal broadcasting** -- emit signals from server to all linked clients
- **Transport-agnostic** -- works over WebSocket, TCP, or any bidirectional text channel
- **Zero runtime dependencies** -- uses only the Python standard library
- **Lightweight wire format** -- messages are JSON-serialized arrays for minimal overhead

## Installation

```bash
pip install olink-core
```

Requires Python 3.9 or later.

## Quick Start

ObjectLink uses two roles: a **source** (server-side object) and a **sink** (client-side proxy). A `RemoteNode` manages the server protocol, and a `ClientNode` manages the client protocol. You connect them by wiring each node's output to the other's input.

### Define a source (server side)

A source implements `IObjectSource` and exposes an object's properties and methods to remote clients.

```python
from typing import Any
from olink.core.types import Name
from olink.remote import IObjectSource, RemoteNode


class Counter:
    count = 0

    def increment(self):
        self.count += 1
        RemoteNode.notify_property_change("demo.Counter/count", self.count)


class CounterSource(IObjectSource):
    def __init__(self, impl: Counter):
        self.impl = impl
        RemoteNode.register_source(self)

    def olink_object_name(self) -> str:
        return "demo.Counter"

    def olink_invoke(self, name: str, args: list[Any]) -> Any:
        path = Name.path_from_name(name)
        if path == "increment":
            return self.impl.increment()
        return None

    def olink_set_property(self, name: str, value: Any):
        path = Name.path_from_name(name)
        if path == "count":
            self.impl.count = value

    def olink_linked(self, name: str, node: RemoteNode):
        pass  # called when a client links

    def olink_unlinked(self, name: str, node: RemoteNode):
        pass  # called when a client unlinks

    def olink_collect_properties(self) -> object:
        return {"count": self.impl.count}
```

### Define a sink (client side)

A sink implements `IObjectSink` and receives property changes, invoke replies, and signals from the remote source.

```python
from typing import Any
from olink.client import ClientNode, IObjectSink


class CounterSink(IObjectSink):
    count = 0

    def __init__(self):
        self.node = ClientNode.register_sink(self)

    def increment(self):
        if self.node:
            self.node.invoke_remote("demo.Counter/increment", [], None)

    def olink_object_name(self) -> str:
        return "demo.Counter"

    def olink_on_init(self, name: str, props: object, node: ClientNode):
        self.count = props.get("count", 0)
        self.node = node

    def olink_on_property_changed(self, name: str, value: Any):
        self.count = value

    def olink_on_signal(self, name: str, args: list[Any]):
        pass

    def olink_on_release(self):
        self.node = None
```

### Wire the nodes together

For in-process testing or local use, connect the nodes directly:

```python
from olink.client import ClientNode
from olink.remote import RemoteNode

client = ClientNode()
remote = RemoteNode()

# Wire output of each node to the input of the other
client.on_write(lambda msg: remote.handle_message(msg))
remote.on_write(lambda msg: client.handle_message(msg))

# Create source and sink
counter = Counter()
source = CounterSource(counter)
sink = CounterSink()

# Link the client to the remote object
client.link_remote("demo.Counter")

# Invoke a method -- the source receives the call, updates state,
# and broadcasts the property change back to the sink
sink.increment()
print(sink.count)  # 1
```

For real network use, plug `on_write` into your WebSocket (or other transport) send path and feed received messages into `handle_message`. See the [`examples/`](examples/) directory for a complete WebSocket client and server using [Starlette](https://www.starlette.io) and [websockets](https://websockets.readthedocs.io).

## Architecture

```
Client Side                          Server Side
+-------------+                      +-------------+
| IObjectSink |  <-- property/signal | IObjectSource|
|  (your code)|      notifications   |  (your code) |
+------+------+                      +------+-------+
       |                                    |
+------+------+    JSON messages     +------+-------+
| ClientNode  | <==================> | RemoteNode   |
+------+------+   (any transport)    +------+-------+
       |                                    |
+------+------+                      +------+-------+
|ClientRegistry|                     |RemoteRegistry|
+--------------+                     +--------------+
```

### Package structure

| Package | Purpose |
|---|---|
| `olink.core` | Wire protocol, message types, base node, naming utilities |
| `olink.client` | `ClientNode`, `ClientRegistry`, `IObjectSink` interface |
| `olink.remote` | `RemoteNode`, `RemoteRegistry`, `IObjectSource` interface |
| `olink.mocks` | `MockSink` and `MockSource` for testing |

### Wire protocol

Messages are JSON arrays where the first element is an integer message type:

| Type | Code | Format |
|---|---|---|
| Link | 10 | `[10, "object.Name"]` |
| Init | 11 | `[11, "object.Name", {properties}]` |
| Unlink | 12 | `[12, "object.Name"]` |
| SetProperty | 20 | `[20, "object.Name/prop", value]` |
| PropertyChange | 21 | `[21, "object.Name/prop", value]` |
| Invoke | 30 | `[30, requestId, "object.Name/method", [args]]` |
| InvokeReply | 31 | `[31, requestId, "object.Name/method", returnValue]` |
| Signal | 40 | `[40, "object.Name/signal", [args]]` |
| Error | 90 | `[90, msgType, requestId, "error message"]` |

Object names follow the pattern `module.Interface` (e.g., `demo.Counter`). Property, method, and signal names append a path: `demo.Counter/count`, `demo.Counter/increment`.

## Development

### Setup

```bash
git clone https://github.com/apigear-io/objectlink-core-python.git
cd objectlink-core-python
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=olink --cov-report=term-missing
```

### Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting:

```bash
ruff format --check .
ruff check .
```

### Running the demo server

Install the optional example dependencies and start the WebSocket server:

```bash
pip install -e ".[examples]"
uvicorn demo_server:app --port=8080
```

## Test Matrix

CI runs on every push and pull request against `main`:

| | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|---|---|---|---|---|---|
| Ubuntu | yes | yes | yes | yes | yes |
| macOS | yes | yes | yes | yes | yes |
| Windows | yes | yes | yes | yes | yes |

Coverage reports are generated on Python 3.12 / Ubuntu.

## Contributing

Contributions are welcome. To get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make your changes and add tests
5. Verify formatting and tests pass: `ruff format --check . && ruff check . && pytest`
6. Open a pull request against `main`

## License

This project is licensed under the [MIT License](LICENSE).
