#!/usr/bin/env python3
"""Минимальный HTTP-сервер для примера zmqgate (серверит static/index.html)."""
import argparse
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # pragma: no cover - minimal logging
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the zmqgate web client")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="адрес, на котором слушать HTTP",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="порт HTTP-сервера",
    )
    parser.add_argument(
        "--directory",
        default="webclient",
        help="директория с index.html",
    )
    args = parser.parse_args()

    script_dir = os.path.abspath(os.path.dirname(__file__))
    directory = os.path.join(script_dir, args.directory)
    if not os.path.isdir(directory):
        print(f"{directory} не найдена", file=sys.stderr)
        sys.exit(1)

    handler = partial(QuietHandler, directory=directory)
    server_address = (args.host, args.port)
    with ThreadingHTTPServer(server_address, handler) as httpd:
        print(f"Serving {directory} on http://{args.host}:{args.port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("выход")
        finally:
            httpd.server_close()


if __name__ == "__main__":
    main()
