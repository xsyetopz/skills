"""Fetch one scholarly provider's native metadata without merging identities.

Stdlib only. Writes raw Atom/XML (arXiv) or raw JSON (Crossref/OpenAlex).
Does not fetch papers, interpret results, or silently use stale caches.
Exit 0: valid response (possibly zero results); 1: request/output failure;
2: invalid invocation. OPENALEX_API_KEY is optional and never put in the URL.
"""

from __future__ import annotations

import argparse
import email.utils
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
RETRYABLE = {429, 500, 502, 503, 504}
LIMIT_BYTES = 16 * 1024 * 1024


class FetchError(RuntimeError):
    pass


def request_for(
    provider: str,
    query: str | None,
    identifier: str | None,
    limit: int,
    extra: list[str],
    *,
    key: str | None = None,
    mailto: str | None = None,
) -> urllib.request.Request:
    if (query is None) == (identifier is None):
        raise ValueError("provide exactly one query or identifier")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if not (query or identifier or "").strip():
        raise ValueError("query/identifier must not be empty")
    headers = {"User-Agent": "agent-skills-metadata/2", "Accept": "application/json"}
    if provider == "arxiv":
        url = "https://export.arxiv.org/api/query"
        if identifier and not re.fullmatch(
            r"(?:[0-9]{4}\.[0-9]{4,5}|[a-zA-Z-]+(?:\.[A-Z]{2})?/[0-9]{7})(?:v[1-9][0-9]*)?",
            identifier,
        ):
            raise ValueError("use a bare arXiv ID, preserving any requested vN suffix")
        params = {"id_list": identifier} if identifier else {"search_query": query}
        params.update(start="0", max_results=str(limit))
        headers["Accept"] = "application/atom+xml"
    elif provider == "crossref":
        url = "https://api.crossref.org/works"
        if identifier:
            if not re.fullmatch(r"10\.[0-9]{4,9}/\S+", identifier):
                raise ValueError(
                    "Crossref --id requires a bare DOI; punctuation is not trimmed"
                )
            url += "/" + urllib.parse.quote(identifier, safe="")
            params = {}
        else:
            params = {"query.bibliographic": query, "rows": str(limit)}
        if mailto:
            params["mailto"] = mailto
    elif provider == "openalex":
        url = "https://api.openalex.org/works"
        if identifier:
            if not re.fullmatch(r"W[0-9]+", identifier):
                raise ValueError("OpenAlex --id requires a work ID such as W2741809807")
            url += "/" + identifier
            params = {}
        else:
            params = {"search": query, "per_page": str(limit)}
        if key:
            headers["Authorization"] = "Bearer " + key
    else:
        raise ValueError("unsupported provider")
    for item in extra:
        name, sep, value = item.partition("=")
        if not sep or not name:
            raise ValueError("--param requires NAME=VALUE")
        if name in params:
            raise ValueError(f"duplicate/conflicting native parameter: {name}")
        if name.casefold() in {"api_key", "apikey", "key", "token", "access_token"}:
            raise ValueError(
                "do not put credentials in parameters; use OPENALEX_API_KEY"
            )
        params[name] = value
    if key and any(c in key for c in "\r\n"):
        raise ValueError("invalid credential header")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return urllib.request.Request(url, headers=headers)


def validate_response(provider: str, body: bytes) -> None:
    """Check the native envelope; do not rewrite provider fields or paper versions."""
    if provider == "arxiv":
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise FetchError("arXiv did not return well-formed Atom XML") from exc
        if root.tag != ATOM + "feed":
            raise FetchError("arXiv response is not an Atom feed")
        for entry in root.findall(ATOM + "entry"):
            if "/api/errors" in entry.findtext(ATOM + "id", ""):
                raise FetchError(
                    "arXiv returned an API error entry; check native query syntax"
                )
    else:
        try:
            value = json.loads(body)
        except (ValueError, UnicodeError) as exc:
            raise FetchError(f"{provider} did not return JSON") from exc
        if not isinstance(value, dict):
            raise FetchError(f"{provider} response must be a JSON object")
        if provider == "crossref" and (
            value.get("status") != "ok" or "message" not in value
        ):
            raise FetchError("Crossref returned an unsuccessful/unknown envelope")
        if provider == "openalex" and not (
            "id" in value or isinstance(value.get("results"), list)
        ):
            raise FetchError("OpenAlex returned an unsuccessful/unknown envelope")


def retry_delay(header: str | None, attempt: int, minimum: float) -> float:
    if header:
        try:
            delay = float(header)
        except ValueError:
            try:
                delay = (
                    email.utils.parsedate_to_datetime(header).timestamp() - time.time()
                )
            except (ValueError, TypeError, OverflowError):
                delay = float(2**attempt)
        if not math.isfinite(delay):
            delay = float(2**attempt)
        return max(minimum, delay)
    return max(minimum, float(2**attempt))


def fetch(
    request: urllib.request.Request,
    provider: str,
    *,
    timeout: float = 20,
    attempts: int = 3,
    max_wait: float = 30,
    opener=None,
    sleeper=time.sleep,
) -> bytes:
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    for attempt in range(attempts):
        try:
            with opener(request, timeout=timeout) as response:
                # The default and CLI openers refuse authenticated redirects.
                body = response.read(LIMIT_BYTES + 1)
            if len(body) > LIMIT_BYTES:
                raise FetchError(
                    "response exceeds 16 MiB; narrow the query or use native bulk access"
                )
            validate_response(provider, body)
            return body
        except urllib.error.HTTPError as exc:
            status = exc.code
            delay_header = exc.headers.get("Retry-After") if exc.headers else None
            exc.close()
            if status not in RETRYABLE or attempt + 1 == attempts:
                raise FetchError(
                    f"{provider}: HTTP {status}; no cached response substituted"
                ) from None
            delay = retry_delay(delay_header, attempt, 3 if provider == "arxiv" else 0)
            if delay > max_wait:
                raise FetchError(
                    f"{provider}: server retry delay exceeds --max-wait; retry later, not earlier"
                ) from exc
            sleeper(delay)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Network/environment failures are not missing papers. Avoid hiding a
            # bad proxy/DNS/TLS setup behind repeated requests or stale data.
            raise FetchError(
                f"{provider}: transport failure ({type(exc).__name__}); no cached response substituted"
            ) from None
    raise FetchError("no request attempted")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FetchError(
            f"HTTP {code} redirect refused; verify the provider endpoint before following it"
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", required=True, choices=["arxiv", "crossref", "openalex"]
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--query", help="native query text; arXiv uses its own field/query syntax"
    )
    target.add_argument(
        "--id",
        dest="identifier",
        help="bare arXiv ID (including vN), DOI, or OpenAlex work ID",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="additional native NAME=VALUE; duplicates fail",
    )
    parser.add_argument(
        "--mailto", help="optional Crossref contact; never inferred from local identity"
    )
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--max-wait", type=float, default=30)
    parser.add_argument(
        "--output",
        type=Path,
        help="new file; never overwrites an existing file (default: raw stdout)",
    )
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if (
        not math.isfinite(args.max_wait)
        or args.max_wait < 0
        or not 1 <= args.attempts <= 5
    ):
        parser.error(
            "--max-wait must be finite/non-negative; --attempts must be in 1..5"
        )
    if args.mailto and args.provider != "crossref":
        parser.error("--mailto is a Crossref-specific control")
    try:
        request = request_for(
            args.provider,
            args.query,
            args.identifier,
            args.limit,
            args.param,
            key=os.getenv("OPENALEX_API_KEY") if args.provider == "openalex" else None,
            mailto=args.mailto,
        )
    except ValueError as exc:
        parser.error(str(exc))
    try:
        body = fetch(
            request,
            args.provider,
            timeout=args.timeout,
            attempts=args.attempts,
            max_wait=args.max_wait,
            opener=urllib.request.build_opener(NoRedirect()).open,
        )
        if args.output:
            with args.output.open("xb") as stream:
                stream.write(body)
        else:
            sys.stdout.buffer.write(body)
    except (FetchError, OSError) as exc:
        print(f"metadata fetch failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
