#!/usr/bin/env python3
"""Простой сервер-бот, подключается к zmqgate по TCP.

Отправляет дублирующее сообщение на несуществующий conid, чтобы проверить
режим игнорирования неизвестных соединений в zmqgate.
"""
import argparse
import json
import logging
import random
import os
import signal
import sys
import uuid
from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import quote

import zmq

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

NICK_FRAGMENTS = [
    "Atlas",
    "Bolt",
    "Crimson",
    "Drift",
    "Echo",
    "Flare",
    "Glint",
    "Hush",
    "Ivy",
    "Jolt",
    "Kite",
    "Lumen",
    "Muse",
    "Nova",
    "Orbit",
    "Pulse",
    "Quill",
    "Rune",
    "Sage",
    "Tide",
    "Umber",
    "Vega",
    "Wisp",
    "Zephyr",
]


def _avatar_for(nick: str) -> str:
    return (
        "https://api.dicebear.com/9.x/croodles/svg?"
        f"seed=ChetirdesatVPN-User{quote(nick)}&backgroundColor=ffd5dc"
    )


@dataclass
class ClientInfo:
    uid: str
    nick: str
    avatar: str


def encode_payload(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    try:
        return json.dumps(value).encode("utf-8")
    except Exception:
        return str(value).encode("utf-8")


class Bot:
    def __init__(self, forward_address: str, output_address: str):
        self.ctx = zmq.Context()
        self.pull = self.ctx.socket(zmq.SUB)
        self.pull.connect(forward_address)
        self.pull.setsockopt(zmq.SUBSCRIBE, b"")
        self.output = self.ctx.socket(zmq.PUB)
        self.output.connect(output_address)
        self.clients: set[bytes] = set()
        self.client_info: Dict[bytes, ClientInfo] = {}
        self.forward_address = forward_address
        self.output_address = output_address
        self.fake_cid: bytes | None = None
        log.info("bot listening %s -> %s", forward_address, output_address)
        self._running = True

    def _generate_nick(self) -> str:
        existing = {info.nick for info in self.client_info.values()}
        while True:
            nick = f"{random.choice(NICK_FRAGMENTS)}{random.randint(100, 999)}"
            if nick not in existing:
                return nick

    def _register_client(self, cid: bytes) -> ClientInfo:
        nick = self._generate_nick()
        info = ClientInfo(uid=str(uuid.uuid4()), nick=nick, avatar=_avatar_for(nick))
        self.clients.add(cid)
        self.client_info[cid] = info
        return info

    def _unregister_client(self, cid: bytes) -> None:
        self.clients.discard(cid)
        self.client_info.pop(cid, None)

    def _client_directory(self) -> list[dict[str, str]]:
        return [
            {"id": info.uid, "nick": info.nick, "avatar": info.avatar}
            for info in self.client_info.values()
        ]

    def _broadcast_clients(self) -> None:
        self.broadcast({
            "event": "clients",
            "clients": self._client_directory(),
        })

    def _broadcast_presence(self, action: str, nick: str) -> None:
        self.broadcast({
            "event": "presence",
            "type": action,
            "nick": nick,
        })

    def _send_welcome(self, cid: bytes, info: ClientInfo) -> None:
        self.send(cid, {
            "event": "welcome",
            "you": {"id": info.uid, "nick": info.nick, "avatar": info.avatar},
            "clients": self._client_directory(),
        })

    def _find_client_by_identifier(self, identifier: str) -> bytes | None:
        for cid, info in self.client_info.items():
            if info.uid == identifier or info.nick.lower() == identifier.lower():
                return cid
        return None

    def run(self) -> None:
        poller = zmq.Poller()
        poller.register(self.pull, zmq.POLLIN)
        while self._running:
            try:
                socks = dict(poller.poll(500))
            except zmq.ZMQError:
                break
            if self.pull in socks:
                msg = self.pull.recv_multipart()
                self.handle(msg)
        self._cleanup()

    def handle(self, msg: list[bytes]) -> None:
        if not msg:
            return
        kind = msg[1] if len(msg) > 1 else b""
        cid = msg[0]
        if kind == b"connect":
            info = self._register_client(cid)
            log.info("connection %s (%s) → connected", cid.hex(), info.nick)
            self._broadcast_presence("joined", info.nick)
            self._broadcast_clients()
            self._send_welcome(cid, info)
            return
        if kind == b"disconnect":
            log.info("connection %s → disconnected", cid.hex())
            info = self.client_info.get(cid)
            self._unregister_client(cid)
            if info:
                self._broadcast_presence("left", info.nick)
            self._broadcast_clients()
            return
        if kind != b"message" or len(msg) < 3:
            return
        data = msg[2]
        try:
            payload = json.loads(data.decode("utf-8"))
        except Exception:
            log.warning("ignore malformed payload: %r", data)
            return
        if not isinstance(payload, dict):
            return
        command = payload.get("command", "")
        sender_info = self.client_info.get(cid)
        sender_nick = sender_info.nick if sender_info else "Guest"
        text = payload.get("text", "")
        if command == "ping":
            self.send(cid, {"event": "reply", "reply": "pong"})
        elif command == "echo":
            self.send(cid, {"event": "reply", "reply": "echo", "text": text})
        elif command == "broadcast":
            if not text:
                self.send(cid, {"event": "error", "message": "Provide text to broadcast."})
                return
            self.broadcast({
                "event": "message",
                "scope": "global",
                "from": sender_nick,
                "text": text,
            })
        elif command == "help":
            self.send(cid, {
                "event": "info",
                "message": "Commands: /help /ping /echo <text> /broadcast <text> /clients /msg <nick|uuid> <text>",
            })
        elif command == "clients":
            self.send(cid, {
                "event": "clients",
                "clients": self._client_directory(),
                "you": {"id": sender_info.uid, "nick": sender_nick} if sender_info else None,
            })
        elif command == "direct":
            target = payload.get("target")
            if not target:
                self.send(cid, {"event": "error", "message": "Specify target nick or uuid."})
                return
            target_cid = self._find_client_by_identifier(target)
            if not target_cid:
                self.send(cid, {"event": "error", "message": f"Client not found: {target}"})
                return
            target_info = self.client_info.get(target_cid)
            target_uid = target_info.uid if target_info else target
            message_payload = {
                "event": "message",
                "scope": "direct",
                "from": sender_nick,
                "text": text,
                "target": target_uid,
            }
            target_packet = dict(message_payload)
            target_packet["self"] = False
            sender_packet = dict(message_payload)
            sender_packet["self"] = True
            sender_packet["target_nick"] = target_info.nick if target_info else target
            self.send(target_cid, target_packet)
            self.send(cid, sender_packet)
        else:
            self.send(cid, {"event": "error", "message": f"Unknown command: {command}"})

    def send(self, cid: bytes, payload: Any) -> None:
        self.output.send_multipart((b"send", cid, encode_payload(payload)))
        if self.fake_cid is None:
            self.fake_cid = os.urandom(len(cid))
        log.info("sending to fake cid %s", self.fake_cid.hex())
        self.output.send_multipart((b"send", self.fake_cid, encode_payload(payload)))

    def broadcast(self, payload: Any, exclude: set[bytes] | None = None) -> None:
        targets = list(self.clients)
        if exclude:
            targets = [client for client in targets if client not in exclude]
        for client in targets:
            self.send(client, payload)

    def stop(self, *args: Any) -> None:
        log.info("остановка бота")
        self._running = False

    def _cleanup(self) -> None:
        try:
            self.pull.close()
            self.output.close()
            self.ctx.term()
        except Exception:
            pass

    def _client_directory(self) -> list[dict[str, str]]:
        return [
            {"id": cid.hex(), "nick": info.nick, "avatar": info.avatar}
            for cid, info in self.client_info.items()
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot, подключенный к zmqgate по TCP")
    parser.add_argument(
        "--forward",
        default="tcp://127.0.0.1:9001",
        help="адрес, куда zmqgate отправляет websocket-сообщения",
    )
    parser.add_argument(
        "--output",
        default="tcp://127.0.0.1:9002",
        help="адрес, куда бот публикует ответы",
    )
    args = parser.parse_args()
    bot = Bot(args.forward, args.output)
    signal.signal(signal.SIGINT, bot.stop)
    signal.signal(signal.SIGTERM, bot.stop)
    bot.run()


if __name__ == "__main__":
    main()
