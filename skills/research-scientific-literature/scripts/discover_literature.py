#!/usr/bin/env python3
"""Discover scholarly metadata without inferring scientific conclusions."""

from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from html.parser import HTMLParser
from pathlib import Path
from types import TracebackType
from typing import Protocol, TypedDict

ARXIV_ID = re.compile(
    r"(?:arxiv:|/abs/)?((?:[a-z-]+(?:\.[A-Z]{2})?/)?\d{4}\.\d{4,5}|[a-z-]+/\d{7})(v\d+)?$",
    re.IGNORECASE,
)
DOI = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?(10\.\d{4,9}/\S+)$", re.IGNORECASE
)
RETRYABLE = {429, 500, 502, 503, 504}
USER_AGENT = "xsyetopz-literature-discovery/1.0 (https://github.com/xsyetopz/skills)"
ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}


class FetchError(RuntimeError):
    pass


class HeaderLookup(Protocol):
    def get(self, name: str, default: str | None = None) -> str | None: ...


class ReadableResponse(Protocol):
    @property
    def headers(self) -> HeaderLookup: ...

    def read(self) -> bytes: ...

    def __enter__(self) -> ReadableResponse: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class LiteratureRecord(TypedDict):
    title: str
    authors: list[str]
    year: str | None
    abstract: str
    identifiers: dict[str, str]
    arxiv_version: str | None
    publication: str | None
    sources: list[str]
    links: list[str]


RecordParser = Callable[[bytes], list[LiteratureRecord]]


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    match = DOI.search(value.strip().rstrip(".,;)"))
    return match.group(1).lower() if match else None


def normalize_arxiv(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    match = ARXIV_ID.search(value.strip())
    if not match:
        return None, None
    return match.group(1).lower(), match.group(2).lower() if match.group(2) else None


def title_key(value: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", value.casefold()).split())


class CachedFetcher:
    def __init__(
        self,
        cache_dir: Path,
        *,
        offline: bool = False,
        timeout: float = 12,
        attempts: int = 3,
        opener: Callable[..., ReadableResponse] = urllib.request.urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.cache_dir = cache_dir
        self.offline = offline
        self.timeout = timeout
        self.attempts = attempts
        self.opener = opener
        self.sleeper = sleeper

    def _path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"

    def get(self, url: str) -> bytes:
        path = self._path(url)
        cached = json.loads(path.read_text()) if path.exists() else None
        if self.offline:
            if cached is None:
                raise FetchError(f"offline cache miss: {url}")
            return bytes.fromhex(cached["body"])

        headers = {
            "Accept": "application/json, application/atom+xml",
            "User-Agent": USER_AGENT,
        }
        if cached:
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]
        for attempt in range(self.attempts):
            try:
                response = self.opener(
                    urllib.request.Request(url, headers=headers), timeout=self.timeout
                )
                with response:
                    body = response.read()
                    record = {
                        "url": url,
                        "body": body.hex(),
                        "etag": response.headers.get("ETag"),
                        "last_modified": response.headers.get("Last-Modified"),
                        "fetched_at": int(time.time()),
                    }
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record, sort_keys=True))
                return body
            except urllib.error.HTTPError as error:
                retry_after = error.headers.get("Retry-After")
                code = error.code
                error.close()
                if code == 304 and cached:
                    return bytes.fromhex(cached["body"])
                if code not in RETRYABLE or attempt + 1 == self.attempts:
                    break
                self.sleeper(retry_delay(retry_after, attempt))
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt + 1 == self.attempts:
                    break
                self.sleeper(2**attempt)
        if cached:
            return bytes.fromhex(cached["body"])
        raise FetchError(f"request failed after {self.attempts} attempts: {url}")


def retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return min(30.0, max(0.0, float(value)))
        except ValueError:
            parsed = email.utils.parsedate_to_datetime(value)
            return min(30.0, max(0.0, parsed.timestamp() - time.time()))
    return float(2**attempt)


def arxiv_records(body: bytes) -> list[LiteratureRecord]:
    root = ET.fromstring(body)
    records: list[LiteratureRecord] = []
    for entry in root.findall("a:entry", ATOM):
        identifier, version = normalize_arxiv(entry.findtext("a:id", "", ATOM))
        doi = normalize_doi(entry.findtext("x:doi", "", ATOM))
        links = [
            node.attrib["href"]
            for node in entry.findall("a:link", ATOM)
            if node.attrib.get("href")
        ]
        records.append(
            record(
                title=entry.findtext("a:title", "", ATOM),
                authors=[
                    node.findtext("a:name", "", ATOM)
                    for node in entry.findall("a:author", ATOM)
                ],
                year=(entry.findtext("a:published", "", ATOM) or "")[:4] or None,
                abstract=entry.findtext("a:summary", "", ATOM),
                source="arxiv",
                arxiv=identifier,
                arxiv_version=version,
                doi=doi,
                links=links,
            )
        )
    return records


class ArxivMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, list[str]] = {}
        self.versions: set[int] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        values = dict(attrs)
        name = values.get("name")
        content = values.get("content")
        if name and name.startswith("citation_") and content:
            self.metadata.setdefault(name, []).append(content)

    def handle_data(self, data: str) -> None:
        for version in re.findall(r"\[v(\d+)]", data):
            self.versions.add(int(version))


def arxiv_web_records(body: bytes) -> list[LiteratureRecord]:
    parser = ArxivMetaParser()
    parser.feed(body.decode("utf-8"))
    metadata = parser.metadata
    identifier, version = normalize_arxiv(
        (metadata.get("citation_arxiv_id") or [None])[0]
    )
    if parser.versions:
        version = f"v{max(parser.versions)}"
    if not identifier or not metadata.get("citation_title"):
        return []
    date = (metadata.get("citation_date") or [""])[0]
    return [
        record(
            title=metadata["citation_title"][0],
            authors=metadata.get("citation_author", []),
            year=date[:4] or None,
            abstract=(metadata.get("citation_abstract") or [""])[0],
            source="arxiv-web",
            arxiv=identifier,
            arxiv_version=version,
            doi=normalize_doi((metadata.get("citation_doi") or [None])[0]),
            links=metadata.get("citation_pdf_url", []),
        )
    ]


def crossref_records(body: bytes) -> list[LiteratureRecord]:
    items = json.loads(body)["message"].get("items", [])
    records: list[LiteratureRecord] = []
    for item in items:
        dates = (
            item.get("published-print")
            or item.get("published-online")
            or item.get("issued")
            or {}
        )
        parts = dates.get("date-parts", [[]])
        records.append(
            record(
                title=(item.get("title") or [""])[0],
                authors=[
                    " ".join(filter(None, [a.get("given"), a.get("family")]))
                    for a in item.get("author", [])
                ],
                year=str(parts[0][0]) if parts and parts[0] else None,
                abstract=item.get("abstract", ""),
                source="crossref",
                doi=normalize_doi(item.get("DOI")),
                links=[item.get("URL", "")],
                publication=item.get("container-title", [None])[0],
            )
        )
    return records


def openalex_records(body: bytes) -> list[LiteratureRecord]:
    records: list[LiteratureRecord] = []
    for item in json.loads(body).get("results", []):
        ids = item.get("ids") or {}
        arxiv, version = normalize_arxiv(ids.get("arxiv"))
        location = item.get("primary_location") or {}
        records.append(
            record(
                title=item.get("title", ""),
                authors=[
                    a.get("author", {}).get("display_name", "")
                    for a in item.get("authorships", [])
                ],
                year=str(item["publication_year"])
                if item.get("publication_year")
                else None,
                abstract="",
                source="openalex",
                doi=normalize_doi(ids.get("doi")),
                arxiv=arxiv,
                arxiv_version=version,
                links=[location.get("landing_page_url", ""), item.get("id", "")],
                publication=(location.get("source") or {}).get("display_name"),
            )
        )
    return records


def record(
    *,
    title: str | None,
    authors: Iterable[str],
    year: str | None,
    source: str,
    links: Iterable[str | None],
    abstract: str | None = "",
    doi: str | None = None,
    arxiv: str | None = None,
    arxiv_version: str | None = None,
    publication: str | None = None,
) -> LiteratureRecord:
    return {
        "title": " ".join((title or "").split()),
        "authors": [name for name in authors if name],
        "year": year,
        "abstract": " ".join((abstract or "").split()),
        "identifiers": {
            kind: value
            for kind, value in (("doi", doi), ("arxiv", arxiv))
            if value is not None
        },
        "arxiv_version": arxiv_version,
        "publication": publication,
        "sources": [source],
        "links": [link for link in links if link],
    }


def merge_records(records: list[LiteratureRecord]) -> list[LiteratureRecord]:
    merged: list[LiteratureRecord] = []
    by_identifier: dict[str, LiteratureRecord] = {}
    for item in records:
        keys = [f"{kind}:{value}" for kind, value in item["identifiers"].items()]
        target = next(
            (by_identifier[key] for key in keys if key in by_identifier), None
        )
        if target is None:
            author = item["authors"][0].casefold() if item["authors"] else ""
            target = next(
                (
                    candidate
                    for candidate in merged
                    if title_key(candidate["title"]) == title_key(item["title"])
                    and candidate.get("year") == item.get("year")
                    and author
                    and any(author == name.casefold() for name in candidate["authors"])
                ),
                None,
            )
        if target is None:
            target = item
            merged.append(target)
        else:
            target["authors"] = list(
                dict.fromkeys([*target["authors"], *item["authors"]])
            )
            target["sources"] = list(
                dict.fromkeys([*target["sources"], *item["sources"]])
            )
            target["links"] = list(dict.fromkeys([*target["links"], *item["links"]]))
            target["identifiers"].update(item["identifiers"])
            target["abstract"] = target["abstract"] or item["abstract"]
            target["publication"] = target["publication"] or item["publication"]
            target["arxiv_version"] = target["arxiv_version"] or item["arxiv_version"]
        for kind, value in target["identifiers"].items():
            by_identifier[f"{kind}:{value}"] = target
    return merged


def discover(
    query: str, limit: int, fetcher: CachedFetcher
) -> tuple[list[LiteratureRecord], list[str]]:
    encoded = urllib.parse.quote(query)
    arxiv_id, _ = normalize_arxiv(query)
    urls: list[tuple[str, str, RecordParser]] = []
    if arxiv_id:
        urls.append(
            (
                "arxiv-web",
                f"https://arxiv.org/abs/{arxiv_id}",
                arxiv_web_records,
            )
        )
    urls.append(
        (
            "arxiv",
            "https://export.arxiv.org/api/query?"
            + (f"id_list={arxiv_id}" if arxiv_id else f"search_query=all:{encoded}")
            + f"&start=0&max_results={limit}",
            arxiv_records,
        )
    )
    if not arxiv_id:
        urls.append(
            (
                "crossref",
                f"https://api.crossref.org/works?query.bibliographic={encoded}&rows={limit}&select=DOI,title,author,published-print,published-online,issued,abstract,URL,container-title",
                crossref_records,
            )
        )
    urls.append(
        (
            "openalex",
            f"https://api.openalex.org/works?search={encoded}&per_page={limit}&select=id,doi,title,publication_year,authorships,ids,primary_location",
            openalex_records,
        )
    )
    source_records: list[list[LiteratureRecord]] = []
    errors: list[str] = []
    for source, url, parser in urls:
        try:
            found = parser(fetcher.get(url))
            if arxiv_id and source == "openalex":
                found = [
                    item
                    for item in found
                    if item["identifiers"].get("arxiv") == arxiv_id
                ]
            source_records.append(found)
            if arxiv_id and found:
                break
        except (
            FetchError,
            ET.ParseError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            errors.append(f"{source}: {error}")
    records = [
        items[index]
        for index in range(max((len(items) for items in source_records), default=0))
        for items in source_records
        if index < len(items)
    ]
    return merge_records(records)[:limit], errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Search text, DOI, or arXiv ID")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--cache-dir", type=Path, default=Path.home() / ".cache/literature-discovery"
    )
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    results, errors = discover(
        args.query, args.limit, CachedFetcher(args.cache_dir, offline=args.offline)
    )
    for error in errors:
        print(f"warning: {error}", file=sys.stderr)
    if args.json:
        json.dump(
            {"query": args.query, "records": results, "source_errors": errors},
            sys.stdout,
            indent=2,
        )
        print()
    else:
        for item in results:
            identifiers = ", ".join(f"{k}:{v}" for k, v in item["identifiers"].items())
            print(
                f"{item['title']} ({item.get('year') or 'year unknown'}) [{identifiers}]"
            )
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
