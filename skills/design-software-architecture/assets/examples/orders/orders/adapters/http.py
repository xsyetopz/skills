"""HTTP adapter: maps the service to JSON over HTTP with RFC 9457 errors."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from orders.domain import OrderError
from orders.ports import OrderStore
from orders.service import place_order


def make_handler(store: OrderStore) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: HTTPStatus, body: dict, problem: bool = False) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            kind = "application/problem+json" if problem else "application/json"
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _problem(self, status: HTTPStatus, detail: str) -> None:
            body = {
                "type": "about:blank",
                "title": status.phrase,
                "status": int(status),
                "detail": detail,
            }
            self._send(status, body, problem=True)

        def do_POST(self) -> None:
            if self.path != "/orders":
                return self._problem(HTTPStatus.NOT_FOUND, f"no route {self.path}")
            key = self.headers.get("Idempotency-Key")
            if not key:
                return self._problem(HTTPStatus.BAD_REQUEST, "Idempotency-Key required")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                order = place_order(
                    store, payload.get("customer", ""), payload.get("items", {}), key
                )
            except (ValueError, OrderError) as error:
                return self._problem(HTTPStatus.UNPROCESSABLE_ENTITY, str(error))
            self._send(
                HTTPStatus.CREATED,
                {"order_id": order.order_id, "quantity": order.quantity},
            )

        def do_GET(self) -> None:
            prefix = "/orders/"
            order = (
                store.get(self.path[len(prefix) :])
                if self.path.startswith(prefix)
                else None
            )
            if order is None:
                return self._problem(HTTPStatus.NOT_FOUND, "order not found")
            self._send(
                HTTPStatus.OK,
                {
                    "order_id": order.order_id,
                    "customer": order.customer,
                    "quantity": order.quantity,
                },
            )

        def log_message(self, format: str, *args: object) -> None:
            pass  # keep test output clean

    return Handler


def serve(store: OrderStore, port: int = 0) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))
