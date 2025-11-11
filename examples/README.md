# zmqgate chat example

[Read the Russian version](README_ru.md)

![zmqgate Web Client screenshot](screenshot.png)

This example shows `zmqgate` relaying websocket traffic over TCP to a chat bot. The browser client renders the chat feed and participant list.

## Features

- group chat with highlighted private and system messages  
- participants list with avatars  
- commands (`/help`, `/ping`, `/broadcast`, `/msg <nick|uuid>`, `/clients`, etc.)  
- additional CLI client in `client.py`

## Getting started

```bash
python3 -m pip install -r requirements.txt
zmqgate -c zmqgate-tcp.yaml
python3 bot.py
python3 webclient.py
```

`webclient.py` serves `http://127.0.0.1:8080/` by default; open it in a browser, you can run a few tabs at once. The CLI client (`python3 client.py`) stays optional but is handy for sending commands from the terminal.

## What you can do

1. Connect through the browser, receive a nick and avatar.  
2. Chat with other clients.  
3. Use `/msg <nick|uuid> <text>` to send private messages.  

This minimal example can be extended into richer systems with multiple channels, private messaging, and service-to-service communication flows via `AJAX/WebSocket → ZeroMQ → your service`.
