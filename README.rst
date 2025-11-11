ZMQGate
=======

ZMQGate is a fork of Zerogw (https://github.com/tailhook/zerogw) that
continues the HTTP-to-ZeroMQ gateway functionality while hardening
websocket handling and routing glue. It still listens for HTTP requests,
parses them and forwards them over a ZeroMQ ZMQ_REQ socket, then waits for
a reply and responds with the data received from ZeroMQ.

Since Zerogw 0.3 websocket support has been available: incoming websocket
messages are forwarded via a ZMQ_PUB socket, and commands are received from
a ZMQ_SUB socket. Each websocket client can subscribe to many topics,
receiving either control messages (such as subscription updates) or topic-
specific payloads that are efficiently broadcast only to the clients that
are subscribed.

ZMQGate remains a lean daemon—it is not a general HTTP server (no static
content, no caching or CGI), just routing logic so latency stays low and it
scales well.

Use it for:
 * RPC's
 * REST API's
 * Ajax
 * WebSockets


Resources
---------

* Documentation mirror: https://app.readthedocs.org/projects/zerogw/


Installing
----------

ZMQGate is distributed as source code that you compile with the bundled
waf wrapper. There are no official apt/yum packages, so install the
dependencies listed below and then follow the Compiling section.

We currently support only Linux.

Dependencies
------------

 * linux with kernel at least 2.6.28 (need accept4)
 * libwebsite_ for handling http
 * coyaml_ for handling configuration
 * python3_ needed for coyaml to build configuration parser
 * libzmq_ and libev_ of course
 * libyaml_ for parsing configuration

First two usually compiled statically, so you don't need them at runtime. Same
with python. (Eventually, I'll release a bundle with precompiled configuration
parser and embedded few other libraries for easier compiling :) )

Suggested packages
~~~~~~~~~~~~~~~~~~

On Debian/Ubuntu the following packages satisfy the build- and run-time
requirements::

    sudo apt-get install \
        build-essential pkg-config python3 \
        libzmq3-dev libyaml-dev libev-dev libssl-dev

To run the binaries you only need::

    sudo apt-get install libzmq5 libyaml-0-2 libev4 libssl3

Logging
~~~~~~~

When running inside Docker it is convenient to stream Zerogw logs to
`stdout`.  Set ``Server.error-log.filename`` to ``"-"`` (the default in
``examples/zerogw.yaml``) and messages will appear in ``docker logs``.

.. _libwebsite: http://github.com/tailhook/libwebsite
.. _coyaml: http://github.com/tailhook/coyaml
.. _python3: http://python.org/
.. _libyaml: http://pyyaml.org/wiki/LibYAML
.. _libzmq: http://zeromq.org/
.. _libev: http://software.schmorp.de/pkg/libev.html


Compiling
---------

::

    ./waf configure --prefix=/usr
    ./waf build
    ./waf install
