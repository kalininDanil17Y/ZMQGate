# ZMQGate

[См. английскую версию](README.md)

ZMQGate — это форк Zerogw (https://github.com/tailhook/zerogw), который продолжает идею HTTP-to-ZeroMQ шлюза и улучшает обработку websocket и маршрутизацию. Он слушает HTTP-запросы, пересылает их через ZeroMQ `ZMQ_REQ`, ждёт ответа и переправляет websocket-сообщения через `ZMQ_PUB`/`ZMQ_SUB`.

Используйте его для:
- RPC
- REST API
- Ajax
- WebSockets

## Ресурсы

* Зеркало документации: https://app.readthedocs.org/projects/zerogw/

## Установка

```bash
sudo apt-get install \
    build-essential pkg-config python3 \
    libzmq3-dev libyaml-dev libev-dev libssl-dev
```

Для запуска уже собранных бинарников достаточно:

```bash
sudo apt-get install libzmq5 libyaml-0-2 libev4 libssl3
```

## Логирование

При работе внутри Docker удобно стримить логи `zmqgate` в `stdout`. Установите `Server.error-log.filename` в `"-"` (по умолчанию в `examples/zmqgate.yaml`), тогда сообщения будут выводиться в `docker logs`.

## Компиляция

```bash
./waf configure --prefix=/usr
./waf build
./waf install
```

## Примеры

См. [examples/README_ru.md](examples/README_ru.md) для демонстрации простого чата и веб-клиента.
