# Discovery and evidence

Reviewed 2026-09-12 against the official arXiv API manual, Crossref REST API,
and OpenAlex API documentation. Recheck source policy and fields when changing
the client.

## Discovery sources

The bundled CLI uses three independent keyless metadata routes:

- arXiv Atom API for preprint identifiers, revisions, abstracts, DOI links, and
  primary-category discovery;
- Crossref REST API for registered DOI and publication metadata;
- OpenAlex Works API for broader discovery and identifier linkage.

Crossref recommends a descriptive user agent, caching, serial requests, and
backoff; adding `--mailto` identifies the client to its polite pool. OpenAlex
allows casual keyless access but gives a larger budget with an optional free
key; this skill does not require one. Respect returned limits and do not rotate
identities, scrape around access controls, or repeatedly download papers.

```sh
python3 scripts/discover_literature.py \
  --query 'distributed tracing tail sampling' --limit 8 --json \
  --cache-dir "${XDG_CACHE_HOME:-$HOME/.cache}/literature-discovery"
```

Use exact arXiv IDs or DOIs as additional queries when known. A broad query
should include multiple technical concepts; a second query should seek
counterevidence rather than merely repeat the first wording.

## Version and claim discipline

Normalize arXiv version suffixes for work identity while retaining the fetched
version URL. Normalize DOI case and URL wrappers. Treat DOI linkage as strong
metadata linkage, not proof that preprint and version-of-record text are
identical. Similar titles alone are insufficient when authors or year conflict.

For each decisive work, read the actual methods, results, and limitations.
Record the exact preprint revision or published DOI. Verify whether reported
numbers are absolute or relative, which baseline and dataset produced them, and
whether uncertainty or significance is reported. Search citations and later
work for replication or contradiction, but read those papers independently.

## Acquisition

Prefer publisher or repository HTML when it preserves the complete paper.
Otherwise download the original PDF once and extract searchable text locally.
Use OCR only when text is genuinely unavailable. Treat supplements, code, and
benchmark revisions as separate artifacts with their own provenance. Do not
execute paper code without reviewing its dependencies, data access, and side
effects.

## Failure semantics

Remote discovery may be incomplete, rate-limited, or unavailable. The CLI uses
bounded timeouts, conditional cache reuse, `Retry-After`, and bounded backoff,
then falls through to other sources. `--offline` never accesses the network and
reports cache misses. A zero-result source is not evidence that no literature
exists.

Primary documentation:

- [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html)
- [Crossref API access and authentication][crossref-access]
- [OpenAlex API authentication](https://help.openalex.org/api/authentication/)

[crossref-access]:
  https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
