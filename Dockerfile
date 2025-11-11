FROM debian:bookworm AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        git \
        python3 \
        python3-distutils \
        python3-yaml \
        libzmq3-dev \
        libyaml-dev \
        libev-dev \
        libssl-dev \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/zmqgate

COPY . .

RUN rm -f .lock-waf* && \
    ./waf configure --prefix=/usr && \
    ./waf build && \
    ./waf install --destdir=/tmp/pkg

FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libzmq5 \
        libyaml-0-2 \
        libev4 \
        libssl3 \
        mime-support && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log && touch /var/log/zmqgate.log

COPY --from=builder /tmp/pkg/usr /usr

COPY examples/zmqgate.yaml /etc/zmqgate/zmqgate.yaml

EXPOSE 6941

ENTRYPOINT ["/usr/bin/zmqgate"]
CMD ["-c", "/etc/zmqgate/zmqgate.yaml"]
