#!/usr/bin/env python3
"""Local web UI for the to-do app, backed by the same JSON store as the CLI."""

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from todo import TodoList, DEFAULT_STORE

STATIC_DIR = Path(__file__).parent / "static"
DONE_RE = re.compile(r"^/api/tasks/(\d+)/done$")
TASK_RE = re.compile(r"^/api/tasks/(\d+)$")


class Handler(BaseHTTPRequestHandler):
    store_path = DEFAULT_STORE

    def _todo(self):
        return TodoList(store_path=self.store_path)

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        elif self.path == "/api/tasks":
            self._send_json(200, self._todo().list())
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        if self.path == "/api/tasks":
            text = (data.get("text") or "").strip()
            if not text:
                self._send_json(400, {"error": "text is required"})
                return
            task = self._todo().add(text, due=data.get("due") or None)
            self._send_json(201, task)
            return

        match = DONE_RE.match(self.path)
        if match:
            task_id = int(match.group(1))
            if self._todo().complete(task_id):
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"error": f"no task with id {task_id}"})
            return

        self._send_json(404, {"error": "not found"})

    def do_DELETE(self):
        if self.path == "/api/tasks":
            self._todo().clear()
            self._send_json(200, {"ok": True})
            return

        match = TASK_RE.match(self.path)
        if match:
            task_id = int(match.group(1))
            if self._todo().remove(task_id):
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"error": f"no task with id {task_id}"})
            return
        self._send_json(404, {"error": "not found"})

    def log_message(self, format, *args):
        pass


def build_parser():
    parser = argparse.ArgumentParser(description="Local web UI for the to-do app")
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="Path to the JSON store file")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    Handler.store_path = args.store
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Serving to-do app at {url} (store: {args.store})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
