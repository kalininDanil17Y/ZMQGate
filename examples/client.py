#!/usr/bin/env python3
"""Simple WebSocket client for zmqgate"""
import argparse
import asyncio
import json
import logging
import sys

import websockets

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

HELP_TEXT = """Commands:
  /help              – show this help
  /ping              – ask bot for pong
  /echo <text>       – bot replies only to you
  /broadcast <text>  – send text to everybody
  /clients           – request list of connected users
  /msg <target> <text> – send private message (target by nick or uuid)
  plain text         – sends as broadcast automatically
  /quit              – exit
"""

PROMPT = "client> "


def show_prompt() -> None:
    sys.stdout.write(PROMPT)
    sys.stdout.flush()


def clear_prompt_line() -> None:
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def build_payload(line: str) -> dict:
    raw = line.strip()
    if not raw:
        return {}
    if raw.startswith("/"):
        rest = raw[1:].strip()
        if not rest:
            return {}
        parts = rest.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        if cmd == "help":
            return {"command": "help"}
        if cmd == "ping":
            return {"command": "ping"}
        if cmd == "echo":
            return {"command": "echo", "text": arg}
        if cmd == "broadcast":
            return {"command": "broadcast", "text": arg}
        if cmd == "clients":
            return {"command": "clients"}
        if cmd in ("msg", "direct"):
            if not arg:
                return {}
            target, sep, message = arg.partition(" ")
            if not message:
                return {}
            return {"command": "direct", "target": target, "text": message}
        if cmd == "quit":
            return {"command": "quit", "quit": True}
        return {"command": "echo", "text": raw}
    return {"command": "broadcast", "text": raw}


def format_server_message(data: dict) -> str:
    event = data.get("event")
    if event == "message":
        scope = data.get("scope", "global")
        sender = data.get("from", "server")
        text = data.get("text", "")
        if scope == "direct":
            return f"[DM] {sender}: {text}"
        return f"{sender}: {text}"
    if event == "clients":
        clients = data.get("clients", [])
        you = data.get("you")
        you_text = f" (you: {you.get('nick')} / {you.get('id')})" if you else ""
        header = f"Clients ({len(clients)}){you_text}"
        details = ", ".join([f"{client['nick']} ({client['id'][:8]})" for client in clients])
        return f"{header} → {details if details else 'no one'}"
    if event == "welcome":
        you = data.get("you", {})
        return f"Welcome {you.get('nick', 'guest')}!"
    if event == "presence":
        nick = data.get("nick", "someone")
        action = data.get("type", "joined")
        return f"{nick} has {action} the chat"
    if event == "status":
        return data.get("message", "")
    if event == "info":
        return data.get("message", "")
    if event == "reply":
        if data.get("reply") == "pong":
            return "pong"
        if data.get("reply") == "echo":
            return f"echo: {data.get('text', '')}"
    if event == "error":
        return f"error: {data.get('message', '')}"
    return json.dumps(data, ensure_ascii=False)


async def send_loop(websocket: websockets.WebSocketClientProtocol) -> None:
    loop = asyncio.get_running_loop()
    print(HELP_TEXT)
    while True:
        show_prompt()
        try:
            line = await loop.run_in_executor(None, input)
        except (EOFError, KeyboardInterrupt):
            await websocket.close()
            return
        payload = build_payload(line)
        if not payload:
            continue
        if payload.get("quit"):
            await websocket.close()
            return
        await websocket.send(json.dumps(payload))


async def receive_loop(websocket: websockets.WebSocketClientProtocol) -> None:
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                clear_prompt_line()
                print("server>", message)
                show_prompt()
            else:
                clear_prompt_line()
                print("server>", format_server_message(data))
                show_prompt()
    except websockets.ConnectionClosed:
        log.info("connection to server closed")


async def main_loop(uri: str) -> None:
    print(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            await asyncio.gather(send_loop(websocket), receive_loop(websocket))
    except ConnectionRefusedError:
        log.error("could not connect to %s", uri)
    except Exception as exc:
        log.exception("websocket error: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Командный WebSocket-клиент для zmqgate")
    parser.add_argument(
        "--url",
        default="ws://localhost:8000/ws",
        help="URL websocket, например ws://localhost:8000/ws",
    )
    args = parser.parse_args()
    asyncio.run(main_loop(args.url))


if __name__ == "__main__":
    main()
