# ObjectLink Core Python Protocol Example

To get a running client and server we need to hook up the protocol with a websocket connection and pass messages into the protocol and send messages emitted from the protocol.

The app example shows the client side of the protocol with an ObjectLink client.

The server example show the server side of the example with a ObjectLink service.

# App

The app is a websocket client which sends periodically an increment call to the remote endpoint.
It uses the ObjectLink client to send the increment call to the remote endpoint.
A websocket adapter adapts the client logic to the websocket protocol.
The adapter uses the ObjectLink protocol to handle all the message parsing and flow.

- ClientWebSocketAdapter - connects to server and handles the websocket messages using the ObjectLink protocol.
- CounterSink - is the client implementation as ObjectSink

TODO: might be better to split the sink logic from the client logic. or to define a clean client interface which can be exposed to the outside world

# Server

The server is a websocket async server which handles the websocket connection and the ObjectLink protocol.
The service handles all the messages from the client and sends back the messages to the client using the ObjectLink protocol.
A websocket adapter adapts the service logic to the websocket protocol.
A remote endpoint handles the websocket connection and the communication with the adapter

```
WebSocketServer -> WebSocketEndpoint -> WebSocketAdapter(ObjectLinkProtocol) -> Service
```

- `WebSocketServer` handles all incoming connection. It creates a WebSocketEndpoint for each connection.
- `WebSocketEndpoint` handles the websocket connection and the communication with the adapter.
- `WebSocketAdapter` handles the ObjectLink protocol and wraps the service implementation.
- `Service` is the service implementation.
