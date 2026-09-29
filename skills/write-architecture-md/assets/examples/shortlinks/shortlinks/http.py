"""HTTP front end: POST /links creates a code, GET /<code> redirects."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from shortlinks.store import LinkStore


def make_server(store: LinkStore, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/links":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            url = self.rfile.read(length).decode().strip()
            if urlsplit(url).scheme not in {"http", "https"}:
                self.send_error(400, "only http and https URLs")
                return
            body = store.add(url).encode()
            self.send_response(201)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            target = store.resolve(self.path.lstrip("/"))
            if target is None:
                self.send_error(404)
                return
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
