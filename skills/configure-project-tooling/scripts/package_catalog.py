#!/usr/bin/env python3
"""Query and refresh the verified third-party package catalog.

The catalog holds one JSONL file per ecosystem (npm, crates, nuget, go) under
assets/packages/. Every fact except `domain` is fetched from a registry or
advisory source by `refresh` and `add`; `status` is derived from those facts.
See references/package-catalog.md for the field meanings and the status rule.

Standard library only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import gzip
import html
import importlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Callable, Iterable
from http.client import HTTPException
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
PACKAGES_DIR = SKILL_DIR / "assets" / "packages"
ECOSYSTEMS = ("npm", "crates", "nuget", "go")
FILES = {eco: f"{eco}.jsonl" for eco in ECOSYSTEMS}
USER_AGENT = (
    "xsyetopz-skills-package-catalog/1.0 (+https://github.com/xsyetopz/skills; "
    "catalog refresh script)"
)
STALE_DAYS = 730
DEPRECATION_MAX = 200
GO_ZIP_MAX_BYTES = 20 * 1024 * 1024
MIN_INTERVAL = {"crates.io": 1.1, "api.npmjs.org": 0.6}

ROW_KEYS = (
    "ecosystem",
    "name",
    "domain",
    "status",
    "latest",
    "released",
    "license",
    "repository",
    "archived",
    "pushed",
    "deprecation",
    "replacement",
    "advisories",
    "downloads",
    "deps",
    "traits",
    "verified",
)
FACT_KEYS = (
    "latest",
    "released",
    "license",
    "repository",
    "archived",
    "pushed",
    "deprecation",
    "replacement",
    "advisories",
    "downloads",
    "deps",
    "traits",
)
TRAIT_KEYS = {
    "npm": ("types", "module", "engines"),
    "crates": ("msrv", "noStd", "procMacro"),
    "nuget": ("frameworks", "aot"),
    "go": ("goVersion", "cgo"),
}
STATUS_ORDER = (
    "active",
    "stale",
    "archived",
    "deprecated",
    "prerelease",
    "missing",
)

Facts = dict[str, Any]
Fetcher = Callable[[str, "Context"], Facts]


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


# --- HTTP ------------------------------------------------------------------


class TooLarge(Exception):
    """A download exceeded the size cap."""


class Http:
    """Polite HTTP: timeouts, retries with backoff, per-host spacing."""

    def __init__(self, timeout: float = 30, retries: int = 4) -> None:
        self.timeout = timeout
        self.retries = retries
        self._lock = threading.Lock()
        self._next: dict[str, float] = {}

    def _space(self, host: str) -> None:
        interval = MIN_INTERVAL.get(host)
        if not interval:
            return
        with self._lock:
            now = time.monotonic()
            wait = self._next.get(host, 0.0) - now
            self._next[host] = max(now, self._next.get(host, 0.0)) + interval
        if wait > 0:
            time.sleep(wait)

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
        max_bytes: int | None = None,
        raw: bool = False,
    ) -> tuple[int, bytes]:
        """Return (status, body). 404 and 410 return (status, b'') without retry."""
        request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
        host = urllib.parse.urlsplit(url).hostname or ""
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self._space(host)
            request = urllib.request.Request(url, data=data, headers=request_headers)
            delay = 2.0**attempt
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    length = int(resp.headers.get("Content-Length") or 0)
                    if max_bytes and length > max_bytes:
                        raise TooLarge(url)
                    body = resp.read()
                    if not raw and body[:2] == b"\x1f\x8b":
                        body = gzip.decompress(body)
                    return resp.status, body
            except urllib.error.HTTPError as err:
                if err.code in (404, 410):
                    return err.code, b""
                if err.code not in (429, 500, 502, 503, 504):
                    return err.code, b""
                retry_after = err.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    delay = max(delay, float(retry_after))
                last_error = err
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                HTTPException,
            ) as err:
                last_error = err
            if attempt < self.retries:
                time.sleep(delay)
        raise RuntimeError(
            f"GET {url} failed after {self.retries + 1} attempts: {last_error}"
        )

    def json(self, url: str, **kwargs: Any) -> tuple[int, Any]:
        status, body = self.get(url, **kwargs)
        if status != 200 or not body:
            return status, None
        return status, json.loads(body)

    def text(self, url: str, **kwargs: Any) -> tuple[int, str]:
        status, body = self.get(url, **kwargs)
        return status, body.decode("utf-8", "replace")


# --- Context ---------------------------------------------------------------


class Context:
    """Shared state for one run: HTTP client, GitHub token, advisory sources."""

    def __init__(self, http: Http | None = None, verified: str | None = None) -> None:
        self.http = http or Http()
        self.verified = verified or dt.date.today().isoformat()
        self.github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self._lock = threading.Lock()
        self._github: dict[str, dict[str, Any] | None] = {}
        self._rustsec: dict[str, list[dict[str, Any]]] | None = None
        self._rustsec_dir: tempfile.TemporaryDirectory[str] | None = None
        self._govuln: dict[str, list[str]] | None = None
        self._govuln_docs: dict[str, Any] = {}

    def close(self) -> None:
        if self._rustsec_dir is not None:
            self._rustsec_dir.cleanup()

    def github(self, repository: str | None) -> dict[str, Any] | None:
        """Return {archived, pushed, license} for a github.com URL, or None."""
        if not repository or not self.github_token:
            return None
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repository)
        if not match:
            return None
        key = f"{match[1]}/{match[2]}".lower()
        with self._lock:
            if key in self._github:
                return self._github[key]
        status, doc = self.http.json(
            f"https://api.github.com/repos/{match[1]}/{match[2]}",
            headers={
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        facts: dict[str, Any] | None = None
        if status == 200 and isinstance(doc, dict):
            spdx = (doc.get("license") or {}).get("spdx_id")
            facts = {
                "archived": bool(doc.get("archived")),
                "pushed": (doc.get("pushed_at") or "")[:10] or None,
                "license": None if spdx in (None, "NOASSERTION") else spdx,
            }
        elif status not in (404, 410):
            log(f"warning: GitHub API answered {status} for {key}")
        with self._lock:
            self._github[key] = facts
        return facts

    def rustsec(self) -> dict[str, list[dict[str, Any]]]:
        """Advisories by crate name from a shallow clone of rustsec/advisory-db."""
        with self._lock:
            if self._rustsec is not None:
                return self._rustsec
            self._rustsec_dir = tempfile.TemporaryDirectory(prefix="advisory-db.")
            target = Path(self._rustsec_dir.name) / "db"
            log("cloning https://github.com/rustsec/advisory-db (shallow)")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--depth",
                    "1",
                    "https://github.com/rustsec/advisory-db",
                    str(target),
                ],
                check=True,
                timeout=600,
            )
            self._rustsec = load_rustsec(target / "crates")
            return self._rustsec

    def govuln(self, module: str) -> list[dict[str, Any]]:
        """OSV documents from vuln.go.dev that list the module."""
        with self._lock:
            if self._govuln is None:
                _, index = self.http.json("https://vuln.go.dev/index/modules.json")
                if not isinstance(index, list):
                    raise RuntimeError("vuln.go.dev module index unavailable")
                self._govuln = {
                    e["path"]: [v["id"] for v in e.get("vulns", [])] for e in index
                }
            ids = self._govuln.get(module, [])
        docs = []
        for vuln_id in ids:
            with self._lock:
                doc = self._govuln_docs.get(vuln_id)
            if doc is None:
                _, doc = self.http.json(f"https://vuln.go.dev/ID/{vuln_id}.json")
                with self._lock:
                    self._govuln_docs[vuln_id] = doc
            if doc and not doc.get("withdrawn"):
                docs.append(doc)
        return docs


# --- Shared helpers --------------------------------------------------------


def trim(message: str | None) -> str | None:
    if not message:
        return None
    text = " ".join(str(message).split())
    return text[:DEPRECATION_MAX] or None


def ver_key(version: str) -> tuple[int, ...]:
    core = version.lstrip("vV").split("+")[0].split("-")[0]
    parts = [int(p) if p.isdigit() else 0 for p in core.split(".")]
    return tuple([*parts, 0, 0, 0, 0][:4])


def is_stable(version: str) -> bool:
    return "-" not in version.lstrip("vV").split("+")[0]


def newest_stable(versions: Iterable[str]) -> str | None:
    stable = [v for v in versions if is_stable(v)]
    return max(stable, key=ver_key) if stable else None


def day(timestamp: str | None) -> str | None:
    if not timestamp or timestamp.startswith("1900-01-01"):
        return None
    return timestamp[:10]


def normalize_repo(url: Any) -> str | None:
    """Return a normalized https URL for a repository field, or None."""
    if isinstance(url, dict):
        url = url.get("url")
    if not isinstance(url, str) or not url.strip():
        return None
    url = url.strip()
    shorthand = re.fullmatch(r"(?:github:)?([\w.-]+)/([\w.-]+)", url)
    if shorthand:
        url = f"https://github.com/{shorthand[1]}/{shorthand[2]}"
    url = re.sub(r"^git\+", "", url)
    url = re.sub(r"^(?:git|ssh|http)://(?:git@)?", "https://", url)
    url = re.sub(r"^git@([^:/]+)[:/]", r"https://\1/", url)
    url = re.sub(r"^https://[^/@]+@", "https://", url)
    url = url.split("#")[0].split("?")[0].rstrip("/")
    url = re.sub(r"\.git$", "", url)
    if not url.startswith("https://"):
        return None
    gh = re.match(r"https://(?:www\.)?github\.com/([^/]+)/([^/]+)", url)
    if gh:
        return f"https://github.com/{gh[1]}/{gh[2]}"
    return url


def has_condition(node: Any, key: str) -> bool:
    if isinstance(node, dict):
        return key in node or any(has_condition(v, key) for v in node.values())
    if isinstance(node, list):
        return any(has_condition(v, key) for v in node)
    return False


def load_toml(text: str) -> dict[str, Any]:
    try:
        tomllib = importlib.import_module("tomllib")
    except ModuleNotFoundError as err:
        raise SystemExit(
            "error: the crates ecosystem needs Python 3.11 or newer (tomllib)"
        ) from err
    return tomllib.loads(text)


def named_replacement(message: str | None, own_name: str, pattern: str) -> str | None:
    """Return the replacement a message names explicitly, else None.

    `pattern` must have one capture group holding the candidate name.
    """
    if not message:
        return None
    for match in re.finditer(pattern, message, re.IGNORECASE):
        if match[1].lower() != own_name.lower():
            return match[1]
    return None


# --- Status ----------------------------------------------------------------


def derive_status(facts: Facts, verified: str) -> str:
    """missing > deprecated > archived > prerelease > stale > active, from facts only."""
    if facts.get("missing"):
        return "missing"
    if facts.get("deprecated"):
        return "deprecated"
    if facts.get("archived") is True:
        return "archived"
    if facts.get("prerelease"):
        return "prerelease"
    released = facts.get("released")
    if released:
        age = dt.date.fromisoformat(verified) - dt.date.fromisoformat(released)
        if age.days > STALE_DAYS:
            return "stale"
    return "active"


def make_row(
    ecosystem: str, name: str, domain: str, facts: Facts, verified: str
) -> dict[str, Any]:
    """Build one catalog row in canonical key order from fetched facts."""
    row: dict[str, Any] = {k: None for k in ROW_KEYS}
    row.update(ecosystem=ecosystem, name=name, domain=domain, verified=verified)
    for key in FACT_KEYS:
        if key in facts:
            row[key] = facts[key]
    traits = dict.fromkeys(TRAIT_KEYS[ecosystem])
    traits.update(row["traits"] or {})
    row["traits"] = traits
    row["advisories"] = list(row["advisories"] or [])
    if row["deprecation"]:
        row["deprecation"] = trim(row["deprecation"])
    row["status"] = derive_status(facts, verified)
    return row


# --- npm -------------------------------------------------------------------


def npm_module_kind(manifest: dict[str, Any]) -> str:
    exports = manifest.get("exports")
    has_import = has_condition(exports, "import")
    has_require = has_condition(exports, "require")
    if manifest.get("type") == "module":
        return "dual" if has_require else "esm"
    return "dual" if has_import else "cjs"


NPM_REPLACEMENT = (
    r"(?:use|replaced by|moved to|renamed to|switch to|migrate to)\s+(?:the\s+)?"
    r"(?:[`'\"](@?[a-z0-9][a-z0-9._~/-]*)[`'\"]|(@[a-z0-9._~-]+/[a-z0-9._~-]+)"
    r"|([a-z0-9][a-z0-9._~-]*)(?=\s+instead))"
)


def npm_replacement(message: str | None, name: str, ctx: Context) -> str | None:
    if not message:
        return None
    for match in re.finditer(NPM_REPLACEMENT, message, re.IGNORECASE):
        candidate = match[1] or match[2] or match[3]
        if candidate.lower() == name.lower():
            continue
        status, _ = ctx.http.get(
            "https://registry.npmjs.org/" + urllib.parse.quote(candidate, safe="@"),
            headers={"Accept": "application/vnd.npm.install-v1+json"},
        )
        if status == 200:
            return candidate
    return None


def fetch_npm(name: str, ctx: Context) -> Facts:
    status, doc = ctx.http.json(
        "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@")
    )
    if status in (404, 410) or not isinstance(doc, dict) or not doc.get("versions"):
        return {"missing": True}
    versions = doc["versions"]
    tagged = (doc.get("dist-tags") or {}).get("latest")
    latest = (
        tagged
        if isinstance(tagged, str) and tagged in versions and is_stable(tagged)
        else newest_stable(versions)
    )
    facts: Facts = {"latest": latest}
    if latest is None:
        # No stable release: read deprecation and repository from the tagged or highest prerelease
        # so that a deprecated package is not reported active.
        manifest = versions[
            tagged if tagged in versions else max(versions, key=ver_key)
        ]
        facts["prerelease"] = True
        deprecated = manifest.get("deprecated")
        if deprecated:
            facts["deprecated"] = True
            facts["deprecation"] = trim(str(deprecated))
            facts["replacement"] = npm_replacement(str(deprecated), name, ctx)
        facts["repository"] = normalize_repo(
            manifest.get("repository") or doc.get("repository")
        )
        gh = ctx.github(facts["repository"])
        if gh:
            facts["archived"], facts["pushed"] = gh["archived"], gh["pushed"]
        return facts
    manifest = versions[latest]
    facts["released"] = day((doc.get("time") or {}).get(latest))
    license_value = manifest.get("license")
    if isinstance(license_value, dict):
        license_value = license_value.get("type")
    if not license_value and isinstance(manifest.get("licenses"), list):
        license_value = " OR ".join(
            str(x.get("type"))
            for x in manifest["licenses"]
            if isinstance(x, dict) and x.get("type")
        )
    facts["license"] = (
        license_value if isinstance(license_value, str) and license_value else None
    )
    facts["repository"] = normalize_repo(
        manifest.get("repository") or doc.get("repository")
    )
    deprecated = manifest.get("deprecated")
    if deprecated:
        facts["deprecated"] = True
        facts["deprecation"] = trim(str(deprecated))
        facts["replacement"] = npm_replacement(str(deprecated), name, ctx)
    facts["deps"] = len(manifest.get("dependencies") or {})
    exports = manifest.get("exports")
    bundled = bool(
        manifest.get("types")
        or manifest.get("typings")
        or has_condition(exports, "types")
    )
    engines = manifest.get("engines")
    facts["traits"] = {
        "types": "bundled" if bundled else "none",
        "module": npm_module_kind(manifest),
        "engines": engines if isinstance(engines, dict) else None,
    }
    quoted = urllib.parse.quote(name, safe="@/")
    d_status, downloads = ctx.http.json(
        f"https://api.npmjs.org/downloads/point/last-month/{quoted}"
    )
    facts["downloads"] = (
        downloads.get("downloads") if d_status == 200 and downloads else None
    )
    a_status, advisories = ctx.http.json(
        "https://registry.npmjs.org/-/npm/v1/security/advisories/bulk",
        data=json.dumps({name: [latest]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    ids = []
    if a_status == 200 and isinstance(advisories, dict):
        for adv in advisories.get(name, []):
            url = str(adv.get("url") or "")
            ids.append(
                url.rsplit("/", 1)[-1] if "/advisories/" in url else str(adv.get("id"))
            )
    facts["advisories"] = sorted(set(ids))
    gh = ctx.github(facts["repository"])
    if gh:
        facts["archived"], facts["pushed"] = gh["archived"], gh["pushed"]
    return facts


# --- crates ----------------------------------------------------------------


def _req_bounds(comp: str) -> tuple[str, tuple[int, ...], tuple[int, ...] | None]:
    match = re.fullmatch(
        r"(>=|<=|>|<|=|\^|~)?\s*v?([\d.]+)(?:-[\w.]+)?(?:\.\*)?", comp.strip()
    )
    if not match:
        raise ValueError(f"unsupported version requirement: {comp!r}")
    op = match[1] or "^"
    parts = [int(p) for p in match[2].split(".") if p != ""]
    base = tuple([*parts, 0, 0, 0][:3])
    upper: tuple[int, ...] | None = None
    if op == "^":
        if parts[0] > 0 or len(parts) == 1:
            upper = (base[0] + 1, 0, 0)
        elif len(parts) == 2 or parts[1] > 0:
            upper = (0, base[1] + 1, 0)
        else:
            upper = (0, 0, base[2] + 1)
    elif op == "~":
        upper = (base[0] + 1, 0, 0) if len(parts) == 1 else (base[0], base[1] + 1, 0)
    return op, base, upper


def req_matches(requirement: str, version: str) -> bool:
    """True when `version` satisfies every comma-separated comparator."""
    value = ver_key(version)[:3]
    for comp in requirement.split(","):
        if not comp.strip():
            continue
        op, base, upper = _req_bounds(comp)
        if op in ("^", "~"):
            assert upper is not None
            ok = base <= value < upper
        elif op == "=":
            ok = value == base
        elif op == ">=":
            ok = value >= base
        elif op == ">":
            ok = value > base
        elif op == "<=":
            ok = value <= base
        else:
            ok = value < base
        if not ok:
            return False
    return True


def load_rustsec(crates_dir: Path) -> dict[str, list[dict[str, Any]]]:
    advisories: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(crates_dir.glob("*/RUSTSEC-*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\s*```toml\n(.*?)\n```\n?(.*)", text, re.DOTALL)
        if not match:
            continue
        data = load_toml(match[1])
        adv = data.get("advisory", {})
        versions = data.get("versions", {})
        advisories.setdefault(adv.get("package", path.parent.name), []).append(
            {
                "id": adv["id"],
                "title": adv.get("title", ""),
                "informational": adv.get("informational"),
                "withdrawn": adv.get("withdrawn"),
                "patched": versions.get("patched", []),
                "unaffected": versions.get("unaffected", []),
                "body": match[2],
            }
        )
    return advisories


def rustsec_affecting(
    advisories: list[dict[str, Any]], version: str
) -> list[dict[str, Any]]:
    hits = []
    for adv in advisories:
        if adv.get("withdrawn"):
            continue
        fixed = [*adv.get("patched", []), *adv.get("unaffected", [])]
        if not any(req_matches(r, version) for r in fixed):
            hits.append(adv)
    return hits


RUSTSEC_REPLACEMENT = (
    r"(?:use|replaced by|superseded by|migrate to|switch to|alternatives?(?: include)?)"
    r"[^`\n]{0,20}`([A-Za-z0-9_-]+)`"
)


def crate_proc_macro(ctx: Context, name: str, version: str) -> bool | None:
    """Stream the .crate and read `[lib] proc-macro` from its Cargo.toml."""
    url = f"https://static.crates.io/crates/{name}/{name}-{version}.crate"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with (
            urllib.request.urlopen(request, timeout=ctx.http.timeout) as resp,
            tarfile.open(fileobj=resp, mode="r|gz") as archive,
        ):
            for member in archive:
                if member.name == f"{name}-{version}/Cargo.toml":
                    handle = archive.extractfile(member)
                    if handle is None:
                        return None
                    lib = load_toml(handle.read().decode("utf-8")).get("lib", {})
                    return bool(lib.get("proc-macro") or lib.get("proc_macro"))
    except SystemExit:
        raise
    except (OSError, HTTPException, tarfile.TarError, ValueError):
        return None
    return None


def fetch_crates(name: str, ctx: Context) -> Facts:
    status, doc = ctx.http.json(
        f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}"
    )
    if status in (404, 410) or not isinstance(doc, dict):
        return {"missing": True}
    crate = doc["crate"]
    latest = crate.get("max_stable_version")
    facts: Facts = {
        "latest": latest,
        "repository": normalize_repo(crate.get("repository")),
        "downloads": crate.get("recent_downloads"),
        "prerelease": latest is None,
    }
    slugs = {c.get("slug") for c in doc.get("categories", [])}
    traits: dict[str, Any] = {"noStd": bool(slugs & {"no-std", "no-std::no-alloc"})}
    facts["traits"] = traits
    if latest:
        version = next(v for v in doc["versions"] if v["num"] == latest)
        facts["released"] = day(version.get("created_at"))
        facts["license"] = version.get("license")
        facts["traits"]["msrv"] = version.get("rust_version")
        if version.get("yanked"):
            facts["deprecated"] = True
            facts["deprecation"] = trim(
                "Latest version is yanked. " + (version.get("yank_message") or "")
            )
        d_status, deps = ctx.http.json(
            f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}/{latest}/dependencies"
        )
        if d_status == 200 and deps:
            facts["deps"] = sum(
                1 for d in deps["dependencies"] if d.get("kind") == "normal"
            )
        facts["traits"]["procMacro"] = crate_proc_macro(ctx, name, latest)
        hits = rustsec_affecting(ctx.rustsec().get(name, []), latest)
        facts["advisories"] = sorted(a["id"] for a in hits)
        unmaintained = [a for a in hits if a["informational"] == "unmaintained"]
        if unmaintained:
            adv = unmaintained[0]
            facts["deprecated"] = True
            facts["deprecation"] = trim(adv["title"])
            facts["replacement"] = named_replacement(
                adv["title"] + "\n" + adv["body"][:800], name, RUSTSEC_REPLACEMENT
            )
    gh = ctx.github(facts["repository"])
    if gh:
        facts["archived"], facts["pushed"] = gh["archived"], gh["pushed"]
    return facts


# --- NuGet -----------------------------------------------------------------


def _nuget_entries(ctx: Context, name: str) -> list[dict[str, Any]] | None:
    """Catalog entries of the newest registration page that holds a stable version."""
    status, index = ctx.http.json(
        f"https://api.nuget.org/v3/registration5-gz-semver2/{urllib.parse.quote(name.lower())}/index.json"
    )
    if status in (404, 410) or not isinstance(index, dict):
        return None
    for page in reversed(index.get("items", [])):
        if "items" not in page:
            _, page = ctx.http.json(page["@id"])
        entries = [i["catalogEntry"] for i in (page or {}).get("items", [])]
        if any(is_stable(e["version"]) for e in entries):
            return entries
    return []


def fetch_nuget(name: str, ctx: Context) -> Facts:
    entries = _nuget_entries(ctx, name)
    if entries is None:
        return {"missing": True}
    latest = newest_stable(e["version"] for e in entries)
    if latest is None:
        return {"latest": None, "prerelease": True}
    entry = next(e for e in entries if e["version"] == latest)
    facts: Facts = {
        "latest": latest,
        "released": day(entry.get("published")),
        "license": entry.get("licenseExpression") or None,
    }
    repository = None
    leaf_url = entry.get("@id")
    if leaf_url:
        _, leaf = ctx.http.json(leaf_url)
        if isinstance(leaf, dict):
            repository = normalize_repo(leaf.get("repository"))
    if repository is None:
        # The catalog can drop the nuspec repository element, so read the nuspec itself.
        lowered = name.lower()
        n_status, nuspec = ctx.http.text(
            f"https://api.nuget.org/v3-flatcontainer/{lowered}/{latest.lower()}/{lowered}.nuspec"
        )
        found = re.search(r"<repository\b[^>]*\burl=\"([^\"]+)\"", nuspec or "")
        if n_status == 200 and found:
            repository = normalize_repo(html.unescape(found[1]))
    if repository is None:
        project = normalize_repo(entry.get("projectUrl"))
        if project and "://github.com/" in project:
            repository = project
    facts["repository"] = repository
    deprecation = entry.get("deprecation")
    if deprecation:
        facts["deprecated"] = True
        facts["deprecation"] = trim(
            deprecation.get("message") or ", ".join(deprecation.get("reasons", []))
        )
        facts["replacement"] = (deprecation.get("alternatePackage") or {}).get("id")
    elif entry.get("listed") is False:
        facts["deprecated"] = True
        facts["deprecation"] = "Latest version is unlisted"
    facts["advisories"] = sorted(
        {
            str(v.get("advisoryUrl", "")).rstrip("/").rsplit("/", 1)[-1]
            for v in entry.get("vulnerabilities", [])
        }
        - {""}
    )
    groups = entry.get("dependencyGroups", [])
    facts["deps"] = len(
        {d["id"].lower() for g in groups for d in g.get("dependencies", [])}
    )
    frameworks: list[str] = []
    for group in groups:
        framework = group.get("targetFramework")
        if framework and framework not in frameworks:
            frameworks.append(framework)
    facts["traits"] = {"frameworks": frameworks, "aot": None}
    query = urllib.parse.urlencode(
        {
            "q": f"packageid:{name}",
            "take": 1,
            "prerelease": "true",
            "semVerLevel": "2.0.0",
        }
    )
    s_status, search = ctx.http.json(
        f"https://azuresearch-usnc.nuget.org/query?{query}"
    )
    if s_status == 200 and search and search.get("data"):
        hit = search["data"][0]
        if str(hit.get("id", "")).lower() == name.lower():
            facts["downloads"] = hit.get("totalDownloads")
    gh = ctx.github(facts["repository"])
    if gh:
        facts["archived"], facts["pushed"] = gh["archived"], gh["pushed"]
    return facts


# --- Go --------------------------------------------------------------------

GO_REPLACEMENT = (
    r"(?:use|replaced by|moved to|migrate to|switch to)\s+(?:the\s+)?`?"
    r"((?:[a-z0-9-]+\.)+[a-z]{2,}/[A-Za-z0-9._~/-]*[A-Za-z0-9])"
)


def go_escape(path: str) -> str:
    return re.sub(r"[A-Z]", lambda m: "!" + m.group().lower(), path)


def parse_gomod(text: str, version: str) -> dict[str, Any]:
    """Read go directive, direct requires, deprecation, and retraction."""
    result: dict[str, Any] = {
        "go": None,
        "deps": 0,
        "deprecation": None,
        "retracted": False,
    }
    comments: list[str] = []
    block = ""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("//"):
            comments.append(line[2:].strip())
            continue
        if not line:
            comments.append("")
            continue
        code, _, trailing = line.partition("//")
        code, trailing = code.strip(), trailing.strip()
        if block:
            if code == ")":
                block = ""
                comments = []
                continue
            entry = f"{block} {code}"
        else:
            entry = code
            opener = re.fullmatch(
                r"(require|retract|replace|exclude|tool|godebug)\s*\(", code
            )
            if opener:
                block = opener[1]
                comments = []
                continue
        words = entry.split(None, 1)
        directive = words[0] if words else ""
        if directive == "module":
            paragraph: list[str] = []
            for item in [*comments, ""]:
                if item:
                    paragraph.append(item)
                    continue
                if paragraph and paragraph[0].startswith("Deprecated:"):
                    result["deprecation"] = " ".join(paragraph)
                    break
                paragraph = []
            if result["deprecation"] is None and trailing.startswith("Deprecated:"):
                result["deprecation"] = trailing
        elif directive == "go" and result["go"] is None:
            result["go"] = words[1].strip()
        elif (
            directive == "require"
            and len(words[1].split()) >= 2
            and "indirect" not in trailing
        ):
            result["deps"] += 1
        elif directive == "retract" and _retract_covers(words[1], version):
            result["retracted"] = True
        comments = []
    return result


def _retract_covers(spec: str, version: str) -> bool:
    spec = spec.strip()
    if spec.startswith("["):
        low, _, high = spec.strip("[]").partition(",")
        return ver_key(low.strip()) <= ver_key(version) <= ver_key(high.strip())
    return ver_key(spec) == ver_key(version) and spec.lstrip("v") == version.lstrip("v")


def go_repository(ctx: Context, module: str) -> str | None:
    parts = module.split("/")
    if parts[0] == "github.com" and len(parts) >= 3:
        return f"https://github.com/{parts[1]}/{parts[2]}"
    if parts[0] == "golang.org" and len(parts) >= 3 and parts[1] == "x":
        return f"https://github.com/golang/{parts[2]}"
    status, page = ctx.http.text(f"https://{module}?go-get=1")
    if status != 200:
        return None
    for meta in re.finditer(
        r"<meta\s+name=[\"']go-import[\"']\s+content=[\"']([^\"']+)[\"']", page
    ):
        fields = meta[1].split()
        if len(fields) == 3 and (
            module == fields[0] or module.startswith(fields[0] + "/")
        ):
            return normalize_repo(fields[2])
    return None


def zip_imports_c(blob: bytes) -> bool:
    pattern = re.compile(r'^\s*(?:import\s+)?(?:\w+\s+)?"C"\s*(?://.*)?$', re.MULTILINE)
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for info in archive.infolist():
            is_source = info.filename.endswith(".go") and not info.filename.endswith(
                "_test.go"
            )
            if is_source and pattern.search(
                archive.read(info).decode("utf-8", "replace")
            ):
                return True
    return False


def go_affected(doc: dict[str, Any], module: str, version: str) -> bool:
    value = ver_key(version)
    for affected in doc.get("affected", []):
        if affected.get("package", {}).get("name") != module:
            continue
        if any(
            ver_key(v) == value for v in affected.get("versions", [])
        ) and affected.get("versions"):
            return True
        for rng in affected.get("ranges", []):
            if rng.get("type") != "SEMVER":
                continue
            hit = False
            events = sorted(
                rng.get("events", []), key=lambda e: ver_key(next(iter(e.values())))
            )
            for event in events:
                ((kind, bound),) = event.items()
                if kind == "introduced" and value >= ver_key(bound):
                    hit = True
                elif (kind == "fixed" and value >= ver_key(bound)) or (
                    kind == "last_affected" and value > ver_key(bound)
                ):
                    hit = False
            if hit:
                return True
    return False


def fetch_go(name: str, ctx: Context) -> Facts:
    base = f"https://proxy.golang.org/{go_escape(name)}"
    status, info = ctx.http.json(f"{base}/@latest")
    if status in (404, 410) or not isinstance(info, dict):
        return {"missing": True}
    version, stamp = info["Version"], info["Time"]
    if not is_stable(version):
        _, listing = ctx.http.text(f"{base}/@v/list")
        version = newest_stable(listing.split())  # type: ignore[assignment]
        if version is None:
            return {"latest": None, "prerelease": True, "traits": {}}
        _, info = ctx.http.json(f"{base}/@v/{version}.info")
        stamp = (info or {}).get("Time")
    facts: Facts = {"latest": version, "released": day(stamp)}
    mod_status, mod_text = ctx.http.text(f"{base}/@v/{go_escape(version)}.mod")
    parsed = parse_gomod(mod_text if mod_status == 200 else "", version)
    facts["deps"] = parsed["deps"] if mod_status == 200 else None
    cgo: bool | None = None
    try:
        z_status, blob = ctx.http.get(
            f"{base}/@v/{go_escape(version)}.zip", max_bytes=GO_ZIP_MAX_BYTES, raw=True
        )
        if z_status == 200:
            cgo = zip_imports_c(blob)
    except TooLarge:
        cgo = None
    facts["traits"] = {"goVersion": parsed["go"], "cgo": cgo}
    message = parsed["deprecation"]
    if message:
        message = re.sub(r"^Deprecated:\s*", "", message)
        facts["deprecated"] = True
        facts["deprecation"] = trim(message)
        facts["replacement"] = named_replacement(message, name, GO_REPLACEMENT)
    elif parsed["retracted"]:
        facts["deprecated"] = True
        facts["deprecation"] = "Latest version is retracted"
    facts["advisories"] = sorted(
        d["id"] for d in ctx.govuln(name) if go_affected(d, name, version)
    )
    facts["repository"] = go_repository(ctx, name)
    gh = ctx.github(facts["repository"])
    if gh:
        facts["archived"], facts["pushed"], facts["license"] = (
            gh["archived"],
            gh["pushed"],
            gh["license"],
        )
    return facts


FETCHERS: dict[str, Fetcher] = {
    "npm": fetch_npm,
    "crates": fetch_crates,
    "nuget": fetch_nuget,
    "go": fetch_go,
}


# --- Catalog files ---------------------------------------------------------


def catalog_path(directory: Path, ecosystem: str) -> Path:
    return directory / FILES[ecosystem]


def load_rows(directory: Path, ecosystem: str) -> list[dict[str, Any]]:
    path = catalog_path(directory, ecosystem)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (r["domain"], r["name"]))


def write_rows(directory: Path, ecosystem: str, rows: list[dict[str, Any]]) -> None:
    path = catalog_path(directory, ecosystem)
    text = "".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n"
        for r in sort_rows(rows)
    )
    temp = path.with_suffix(".jsonl.tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)


def load_domains(directory: Path) -> list[str]:
    schema = json.loads((directory / "schema.json").read_text(encoding="utf-8"))
    return list(schema["properties"]["domain"]["enum"])


# --- Refresh and add -------------------------------------------------------


def fetch_rows(
    ecosystem: str,
    targets: list[tuple[str, str]],
    fetch: Fetcher,
    ctx: Context,
    workers: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch rows for (name, domain) pairs; return (rows in input order, failed names)."""
    rows: list[dict[str, Any] | None] = [None] * len(targets)
    failed: list[str] = []

    def work(index: int) -> None:
        name, domain = targets[index]
        try:
            rows[index] = make_row(
                ecosystem, name, domain, fetch(name, ctx), ctx.verified
            )
        except Exception as err:  # noqa: BLE001 - one bad package must not stop the run
            log(f"error: {ecosystem} {name}: {err}")
            failed.append(name)

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for _ in pool.map(work, range(len(targets))):
            done += 1
            if done % 25 == 0 or done == len(targets):
                log(f"{ecosystem}: {done}/{len(targets)}")
    return [r for r in rows if r is not None], failed


def prepare(ecosystem: str, ctx: Context) -> None:
    if not ctx.github_token:
        log(
            "warning: GITHUB_TOKEN and GH_TOKEN are unset; archived and pushed are null (Go license too)"
        )
    if ecosystem == "crates":
        ctx.rustsec()


def cmd_refresh(args: argparse.Namespace, ctx: Context) -> int:
    rows = sort_rows(load_rows(args.catalog_dir, args.ecosystem))
    if not rows:
        log(f"error: no rows in {catalog_path(args.catalog_dir, args.ecosystem)}")
        return 1
    chosen = rows[: args.limit] if args.limit else rows
    prepare(args.ecosystem, ctx)
    fresh, failed = fetch_rows(
        args.ecosystem,
        [(r["name"], r["domain"]) for r in chosen],
        FETCHERS[args.ecosystem],
        ctx,
        args.workers,
    )
    kept = {r["name"]: r for r in rows}
    kept.update({r["name"]: r for r in fresh})  # failed rows keep their previous facts
    write_rows(args.catalog_dir, args.ecosystem, list(kept.values()))
    if failed:
        log(
            f"warning: {len(failed)} rows kept their previous facts: {', '.join(failed)}"
        )
    log(f"wrote {len(kept)} rows to {catalog_path(args.catalog_dir, args.ecosystem)}")
    return 1 if failed else 0


def read_seed(path: Path) -> list[tuple[str, str]]:
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            pairs.append((item["name"], item["domain"]))
    return pairs


def cmd_add(args: argparse.Namespace, ctx: Context) -> int:
    if args.from_file:
        pairs = read_seed(args.from_file)
    elif args.name and args.domain:
        pairs = [(args.name, args.domain)]
    else:
        log("error: give --name and --domain, or --from FILE")
        return 2
    domains = load_domains(args.catalog_dir)
    unknown = sorted({d for _, d in pairs if d not in domains})
    if unknown:
        log(
            f"error: unknown domain(s): {', '.join(unknown)}; see the `domains` subcommand"
        )
        return 2
    rows = load_rows(args.catalog_dir, args.ecosystem)
    present = {r["name"] for r in rows}
    if not args.from_file and pairs[0][0] in present:
        log(f"error: {pairs[0][0]} is already in the catalog; use refresh")
        return 1
    todo = [(n, d) for n, d in pairs if n not in present]
    prepare(args.ecosystem, ctx)
    fresh, failed = fetch_rows(
        args.ecosystem, todo, FETCHERS[args.ecosystem], ctx, args.workers
    )
    write_rows(args.catalog_dir, args.ecosystem, [*rows, *fresh])
    if failed:
        log(
            f"warning: {len(failed)} packages could not be fetched: {', '.join(failed)}"
        )
    log(f"added {len(fresh)} rows, skipped {len(pairs) - len(todo)} already present")
    return 1 if failed else 0


# --- Query -----------------------------------------------------------------


def row_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        0 if row["status"] == "active" else 1,
        -(row["downloads"] or 0),
        row["name"],
    )


def filter_rows(
    rows: list[dict[str, Any]],
    *,
    domain: str | None = None,
    name: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    selected = [
        r
        for r in rows
        if (not domain or r["domain"] == domain)
        and (not name or name.lower() in r["name"].lower())
        and (not status or r["status"] == status)
    ]
    return sorted(selected, key=row_sort_key)


def compact(number: int | None) -> str:
    if number is None:
        return "-"
    for limit, suffix in ((10**9, "B"), (10**6, "M"), (10**3, "k")):
        if number >= limit:
            return f"{number / limit:.1f}{suffix}"
    return str(number)


def format_table(rows: list[dict[str, Any]], with_ecosystem: bool) -> str:
    header = ["name", "domain", "status", "latest", "released", "downloads"]
    if with_ecosystem:
        header.insert(0, "eco")
    body = []
    for r in rows:
        cells = [
            r["name"],
            r["domain"],
            r["status"],
            r["latest"] or "-",
            r["released"] or "-",
            compact(r["downloads"]),
        ]
        if with_ecosystem:
            cells.insert(0, r["ecosystem"])
        body.append(cells)
    widths = [max(len(line[i]) for line in [header, *body]) for i in range(len(header))]
    return "\n".join(
        "  ".join(
            cell.ljust(width) for cell, width in zip(line, widths, strict=True)
        ).rstrip()
        for line in [header, *body]
    )


def selected_ecosystems(value: str | None) -> tuple[str, ...]:
    return (value,) if value else ECOSYSTEMS


def cmd_query(args: argparse.Namespace, _ctx: Context | None = None) -> int:
    rows = [
        r
        for eco in selected_ecosystems(args.ecosystem)
        for r in load_rows(args.catalog_dir, eco)
    ]
    rows = filter_rows(rows, domain=args.domain, name=args.name, status=args.status)
    shown = rows[: args.limit] if args.limit else rows
    if args.json:
        for row in shown:
            print(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
        if len(shown) < len(rows):
            log(
                f"{len(rows) - len(shown)} more rows; raise --limit or narrow the filters"
            )
        return 0
    if not shown:
        print("no matching packages")
        return 0
    print(format_table(shown, args.ecosystem is None))
    if len(shown) < len(rows):
        print(
            f"... {len(rows) - len(shown)} more; narrow the filters or raise --limit (0 = all)"
        )
    return 0


def cmd_domains(args: argparse.Namespace, _ctx: Context | None = None) -> int:
    counts: dict[str, int] = {}
    for eco in selected_ecosystems(args.ecosystem):
        for row in load_rows(args.catalog_dir, eco):
            counts[row["domain"]] = counts.get(row["domain"], 0) + 1
    width = max((len(d) for d in counts), default=0)
    for domain in sorted(counts):
        print(f"{domain.ljust(width)}  {counts[domain]}")
    return 0


# --- CLI -------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query and refresh the verified package catalog."
    )
    parser.add_argument(
        "--catalog-dir",
        type=Path,
        default=PACKAGES_DIR,
        help="directory with the JSONL files",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    query = sub.add_parser("query", help="filter the catalog and print a table")
    query.add_argument("--ecosystem", choices=ECOSYSTEMS)
    query.add_argument("--domain")
    query.add_argument("--name", help="case-insensitive substring of the package name")
    query.add_argument("--status", choices=STATUS_ORDER)
    query.add_argument(
        "--limit", type=int, default=40, help="rows to show, 0 for all (default 40)"
    )
    query.add_argument("--json", action="store_true", help="print JSONL rows")
    query.set_defaults(func=cmd_query)

    domains = sub.add_parser("domains", help="list domains with counts")
    domains.add_argument("--ecosystem", choices=ECOSYSTEMS)
    domains.set_defaults(func=cmd_domains)

    refresh = sub.add_parser("refresh", help="re-fetch every fact for one ecosystem")
    refresh.add_argument("--ecosystem", choices=ECOSYSTEMS, required=True)
    refresh.add_argument(
        "--limit", type=int, default=0, help="refresh only the first N rows"
    )
    refresh.add_argument("--workers", type=int, default=6)
    refresh.set_defaults(func=cmd_refresh)

    add = sub.add_parser("add", help="fetch facts for new packages and insert them")
    add.add_argument("--ecosystem", choices=ECOSYSTEMS, required=True)
    add.add_argument("--name")
    add.add_argument("--domain")
    add.add_argument(
        "--from",
        dest="from_file",
        type=Path,
        help="JSONL of {name, domain} to add in bulk",
    )
    add.add_argument("--workers", type=int, default=6)
    add.set_defaults(func=cmd_add)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in ("refresh", "add"):
        ctx = Context()
        try:
            return args.func(args, ctx)
        finally:
            ctx.close()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
