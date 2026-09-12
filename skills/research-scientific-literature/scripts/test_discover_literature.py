import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

SCRIPT = Path(__file__).with_name("discover_literature.py")
SPEC = importlib.util.spec_from_file_location("discover_literature", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)


class Response(io.BytesIO):
    def __init__(self, body: bytes, headers: dict[str, str] | None = None):
        super().__init__(body)
        self.headers = Message()
        for name, value in (headers or {}).items():
            self.headers[name] = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class LiteratureTests(unittest.TestCase):
    def test_cache_and_conditional_reuse(self):
        # Arrange
        calls = []
        responses = [Response(b"first", {"ETag": '"v1"'})]

        def opener(request, **_kwargs):
            calls.append(request)
            if responses:
                return responses.pop(0)
            raise urllib.error.HTTPError(request.full_url, 304, "", Message(), None)

        with tempfile.TemporaryDirectory() as temporary:
            fetcher = module.CachedFetcher(Path(temporary), opener=opener)
            # Act
            first = fetcher.get("https://example.test/data")
            second = fetcher.get("https://example.test/data")
            # Assert
            self.assertEqual(first, b"first")
            self.assertEqual(second, b"first")
            self.assertEqual(calls[1].headers["If-none-match"], '"v1"')

    def test_offline_hit_and_miss(self):
        # Arrange
        with tempfile.TemporaryDirectory() as temporary:
            online = module.CachedFetcher(
                Path(temporary), opener=lambda *_args, **_kwargs: Response(b"cached")
            )
            online.get("https://example.test/hit")
            offline = module.CachedFetcher(Path(temporary), offline=True)
            # Act
            hit = offline.get("https://example.test/hit")
            # Assert
            self.assertEqual(hit, b"cached")
            with self.assertRaises(module.FetchError):
                offline.get("https://example.test/miss")

    def test_retry_after_then_success(self):
        # Arrange
        sleeps = []
        attempts = 0

        def opener(request, **_kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                headers = Message()
                headers["Retry-After"] = "3"
                raise urllib.error.HTTPError(request.full_url, 429, "", headers, None)
            return Response(b"ok")

        with tempfile.TemporaryDirectory() as temporary:
            fetcher = module.CachedFetcher(
                Path(temporary), opener=opener, sleeper=sleeps.append
            )
            # Act
            body = fetcher.get("https://example.test/retry")
            # Assert
            self.assertEqual(body, b"ok")
            self.assertEqual(sleeps, [3.0])

    def test_source_failure_falls_through(self):
        # Arrange
        crossref = json.dumps(
            {"message": {"items": [{"title": ["Recovered"], "DOI": "10.1/X"}]}}
        ).encode()
        openalex = json.dumps({"results": []}).encode()

        class Fetcher:
            def get(self, url):
                if "arxiv" in url:
                    raise module.FetchError("unavailable")
                return crossref if "crossref" in url else openalex

        # Act
        records, errors = module.discover("query", 5, Fetcher())
        # Assert
        self.assertEqual(records[0]["title"], "Recovered")
        self.assertIn("arxiv: unavailable", errors)

    def test_deduplicates_doi_and_arxiv_revisions(self):
        # Arrange
        records = [
            module.record(
                title="A Paper",
                authors=["A Author"],
                year="2024",
                source="arxiv",
                arxiv="2401.00001",
                arxiv_version="v2",
                doi="10.1234/paper",
                links=[],
            ),
            module.record(
                title="A Paper",
                authors=["A Author"],
                year="2024",
                source="crossref",
                doi="10.1234/PAPER",
                publication="Journal",
                links=[],
            ),
            module.record(
                title="A Paper revised",
                authors=["A Author"],
                year="2024",
                source="openalex",
                arxiv="2401.00001",
                links=[],
            ),
        ]
        # Act
        merged = module.merge_records(records)
        # Assert
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["sources"], ["arxiv", "crossref", "openalex"])
        self.assertEqual(merged[0]["publication"], "Journal")

    def test_ambiguous_titles_do_not_merge(self):
        # Arrange
        records = [
            module.record(
                title="Shared title",
                authors=["One"],
                year="2024",
                source="arxiv",
                links=[],
            ),
            module.record(
                title="Shared title",
                authors=["Two"],
                year="2024",
                source="crossref",
                links=[],
            ),
        ]
        # Act
        merged = module.merge_records(records)
        # Assert
        self.assertEqual(len(merged), 2)

    def test_parses_arxiv_version_and_doi_linkage(self):
        # Arrange
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom"><entry><id>https://arxiv.org/abs/2401.00001v3</id><published>2024-01-01T00:00:00Z</published><title>Paper</title><summary>Claim metadata</summary><author><name>A Author</name></author><arxiv:doi>10.1234/Paper</arxiv:doi><link href="https://arxiv.org/pdf/2401.00001v3" /></entry></feed>"""
        # Act
        records = module.arxiv_records(atom)
        # Assert
        self.assertEqual(
            records[0]["identifiers"], {"doi": "10.1234/paper", "arxiv": "2401.00001"}
        )
        self.assertEqual(records[0]["arxiv_version"], "v3")

    def test_parses_arxiv_web_fallback_metadata(self):
        # Arrange
        html = b"""<html><head><meta name="citation_title" content="Paper"><meta name="citation_author" content="A Author"><meta name="citation_date" content="2024/01/01"><meta name="citation_arxiv_id" content="2401.00001v2"><meta name="citation_pdf_url" content="https://arxiv.org/pdf/2401.00001"></head></html>"""
        # Act
        records = module.arxiv_web_records(html)
        # Assert
        self.assertEqual(records[0]["title"], "Paper")
        self.assertEqual(records[0]["identifiers"]["arxiv"], "2401.00001")
        self.assertEqual(records[0]["arxiv_version"], "v2")


if __name__ == "__main__":
    unittest.main()
