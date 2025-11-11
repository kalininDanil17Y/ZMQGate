# ZMQGate

[Read the Russian version](README_ru.md)

ZMQGate is a fork of Zerogw (https://github.com/tailhook/zerogw) that continues the HTTP-to-ZeroMQ gateway functionality while hardening websocket handling and routing glue. It listens for HTTP requests, forwards them over a ZeroMQ `ZMQ_REQ` socket, waits for replies, and streams websocket commands through `ZMQ_PUB`/`ZMQ_SUB`.

Use it for:
- RPC
- REST APIs
- Ajax
- WebSockets

## Resources

* Documentation mirror: https://app.readthedocs.org/projects/zerogw/

## Installing

```bash
sudo apt-get install \
    build-essential pkg-config python3 \
    libzmq3-dev libyaml-dev libev-dev libssl-dev
```

To run the binaries you only need:

```bash
sudo apt-get install libzmq5 libyaml-0-2 libev4 libssl3
```

## Logging

When running inside Docker it is convenient to stream `zmqgate` logs to `stdout`. Set `Server.error-log.filename` to `"-"` (the default in `examples/zmqgate.yaml`) and messages will appear in `docker logs`.

## Compiling

```bash
./waf configure --prefix=/usr
./waf build
./waf install
```

## Examples

See the [examples/README.md](examples/README.md) for the simple chat/web client demo.
