"""Offline protocol fixtures, not live-provider or scientific-result tests."""

import contextlib
import io
import tempfile
import unittest
import urllib.error
import urllib.parse
from email.message import Message

from fetch_metadata import (
    FetchError,
    fetch,
    main,
    request_for,
    retry_delay,
    validate_response,
)

ATOM = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2401.01234v2</id><title>A &amp; B</title></entry></feed>'


class RequestTests(unittest.TestCase):
    def test_explicit_arxiv_version_survives(self):
        request = request_for("arxiv", None, "2401.01234v2", 10, [])
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
        self.assertEqual(query["id_list"], ["2401.01234v2"])

    def test_native_query_and_parameters_survive(self):
        value = 'ti:"A & B" AND cat:cs.AI'
        request = request_for("arxiv", value, None, 3, ["sortBy=submittedDate"])
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
        self.assertEqual(query["search_query"], [value])
        self.assertEqual(query["sortBy"], ["submittedDate"])

    def test_doi_punctuation_is_not_stripped(self):
        request = request_for("crossref", None, "10.1234/test(1)", 10, [])
        self.assertTrue(request.full_url.endswith("10.1234%2Ftest%281%29"))

    def test_secret_not_in_url_and_unknown_parameter_not_dropped(self):
        request = request_for(
            "openalex",
            "graph",
            None,
            10,
            ["filter=publication_year:2024"],
            key="fixture-key",
        )
        self.assertNotIn("fixture-key", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer fixture-key")
        self.assertIn("filter=", request.full_url)

    def test_invalid_or_conflicting_controls_fail(self):
        for args in [
            ("arxiv", "x", None, 10, ["max_results=2"]),
            ("openalex", "x", None, 10, ["api_key=secret"]),
            ("crossref", None, "not-a-doi", 10, []),
            ("arxiv", None, "2401.01234v0", 10, []),
            ("openalex", "x", None, 0, []),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                request_for(*args)


class ResponseTests(unittest.TestCase):
    def test_native_bytes_preserved(self):
        result = fetch(
            request_for("arxiv", None, "2401.01234v2", 10, []),
            "arxiv",
            opener=lambda *a, **k: io.BytesIO(ATOM),
        )
        self.assertEqual(result, ATOM)

    def test_empty_search_is_a_valid_result(self):
        validate_response("openalex", b'{"meta":{"count":0},"results":[]}')
        validate_response("crossref", b'{"status":"ok","message":{"items":[]}}')

    def test_error_payload_is_not_success(self):
        cases = [
            ("arxiv", b"<html/>"),
            ("openalex", b"[]"),
            ("crossref", b'{"status":"failed","message":{}}'),
            (
                "arxiv",
                b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#bad_query</id></entry></feed>',
            ),
        ]
        for provider, body in cases:
            with self.subTest(provider=provider), self.assertRaises(FetchError):
                validate_response(provider, body)

    def test_retry_after_respected(self):
        headers = Message()
        headers["Retry-After"] = "4"
        calls, sleeps = [], []

        def opener(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.HTTPError(
                    "https://fixture.invalid", 429, "rate limited", headers, None
                )
            return io.BytesIO(ATOM)

        self.assertEqual(
            fetch(
                request_for("arxiv", "all:x", None, 10, []),
                "arxiv",
                opener=opener,
                sleeper=sleeps.append,
            ),
            ATOM,
        )
        self.assertEqual(sleeps, [4])

    def test_no_early_retry_if_server_delay_exceeds_budget(self):
        headers = Message()
        headers["Retry-After"] = "120"

        def opener(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://fixture.invalid", 429, "rate limited", headers, None
            )

        with self.assertRaisesRegex(FetchError, "retry delay"):
            fetch(
                request_for("arxiv", "all:x", None, 10, []),
                "arxiv",
                opener=opener,
                sleeper=lambda _: self.fail("must not retry early"),
            )

    def test_bad_retry_header_does_not_crash(self):
        self.assertEqual(retry_delay("nonsense", 1, 3), 3)
        self.assertEqual(retry_delay("nan", 1, 0), 2)

    def test_transport_failure_is_not_empty_search_or_cache_hit(self):
        def opener(*args, **kwargs):
            raise urllib.error.URLError("sensitive proxy info not echoed")

        with self.assertRaisesRegex(FetchError, "transport failure"):
            fetch(request_for("crossref", "x", None, 10, []), "crossref", opener=opener)


class CommandLineTests(unittest.TestCase):
    def test_existing_output_fails_before_any_request(self):
        with tempfile.NamedTemporaryFile() as existing:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                status = main(
                    [
                        "--provider",
                        "crossref",
                        "--query",
                        "x",
                        "--output",
                        existing.name,
                    ]
                )
        self.assertEqual(status, 1)
        self.assertIn("already exists", err.getvalue())


if __name__ == "__main__":
    unittest.main()
