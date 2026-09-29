import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shortlinks import codes
from shortlinks.http import make_server
from shortlinks.store import LinkStore


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class CodesTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        for number in (0, 61, 62, 3843, 10**9):
            self.assertEqual(codes.decode(codes.encode(number)), number)

    def test_known_value(self) -> None:
        self.assertEqual(codes.encode(62), "10")


class HttpTests(unittest.TestCase):
    def test_create_then_redirect(self) -> None:
        server = make_server(LinkStore(":memory:"), 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_address[1]}"
        request = urllib.request.Request(
            base + "/links", data=b"https://example.org/", method="POST"
        )
        with urllib.request.urlopen(request) as response:
            code = response.read().decode()
        opener = urllib.request.build_opener(NoRedirect)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            opener.open(f"{base}/{code}")
        self.addCleanup(caught.exception.close)
        self.assertEqual(caught.exception.code, 302)
        self.assertEqual(caught.exception.headers["Location"], "https://example.org/")


if __name__ == "__main__":
    unittest.main()
