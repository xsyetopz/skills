"""Stand-in for the internal HTTP client (each call blocks ~50 ms on the network)."""

import threading
import time

_lock = threading.Lock()
in_flight = 0
max_in_flight = 0
calls = 0


def get(url: str) -> dict:
    global in_flight, max_in_flight, calls
    with _lock:
        calls += 1
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
    try:
        time.sleep(0.05)
        if url.endswith("/broken"):
            raise ValueError(f"bad response from {url}")
        return {"url": url, "status": 200}
    finally:
        with _lock:
            in_flight -= 1
