# Find scientific papers and verify bibliographic identity

Use `scripts/fetch_metadata.py` when direct scholarly metadata retrieval is
needed. Python 3.10+ and HTTPS access are required; it uses the standard
library. It fetches **one named provider**, preserves its native response and
does not merge work identities, invent a common schema or substitute stale
cached data.

```sh
python3 scripts/fetch_metadata.py --provider arxiv \
  --query 'all:"tail sampling"' --limit 8 --output arxiv.atom
python3 scripts/fetch_metadata.py --provider arxiv --id 2303.08774v6
python3 scripts/fetch_metadata.py --provider crossref \
  --query 'distributed tracing tail sampling' --limit 8
python3 scripts/fetch_metadata.py --provider openalex \
  --query 'distributed tracing tail sampling' \
  --param 'filter=from_publication_date:2020-01-01' --limit 8
```

The ID in the example is an API-shape example, not evidence relevant to the
query. Bare DOIs are accepted by Crossref and `W...` work IDs by OpenAlex. Do
not strip a requested arXiv version suffix or DOI punctuation. Link versions
explicitly; shared DOI linkage does not prove identical preprint/publisher text.
Similar titles alone are insufficient when authors, venue or year conflict.

Use repeated `--param NAME=VALUE` for additional native query options. Conflicts
and duplicates error rather than silently overriding. `OPENALEX_API_KEY` is an
optional environment credential sent in an Authorization header, never a URL;
`--mailto` is explicit Crossref contact information, never inferred from the
user. Inspect provider rate/budget rules. Space independent arXiv requests at
least three seconds apart; this one-request CLI cannot coordinate separate
processes.

## Exact helper contract

Output is raw Atom/XML for arXiv or raw JSON for Crossref/OpenAlex. `--output`
creates a new file only; it never overwrites an existing file. Otherwise output
goes to stdout, errors to stderr. Exit 0 means a syntactically recognized native
envelope (possibly zero results); 1 is a request/output failure; 2 is bad usage.
It does not validate every record or fetch/read the full papers.

Timeout, retry count and maximum wait are bounded and configurable. HTTP 429 and
selected server errors honor `Retry-After`; a wait exceeding the maximum errors
rather than retrying too early. Redirects are refused to avoid forwarding an
authenticated request to another host. Responses above 16 MiB fail.
Authentication, DNS and malformed response errors do not turn into empty
successful searches. There is no offline-cache mode or automatic fallback
provider; use saved native responses as evidence with their actual acquisition
date, not as a fresh query.

## From metadata to a supported claim

Run a second query seeking contrary evidence, not only synonyms that confirm the
same result. Read decisive methods, results, limitations and exact revisions.
Record sample sizes, baselines, data/model/code versions and uncertainty.
Separate reported effects from your inference and from independently reproduced
results. Use `assets/evidence-note-template.md` when this traceability is
needed.

Prefer full publisher/repository HTML when complete. Otherwise inspect the
actual paper/PDF and its figures/tables. Metadata, abstracts, citation counts
and search rankings are not substitutes for the evidence needed by the claim. Do
not execute paper code without reviewing dependencies and effects. A zero-result
query is not proof of absence of relevant work.

The synthetic responses in `assets/metadata-fixtures/` exercise envelope
handling; they are not fetched papers or research evidence. Run `python3 -m
unittest discover -s scripts -p 'test_*.py' -v` for offline helper tests.

Sources: [user manual][upstream-source-1], [access and
authentication][upstream-source-2], [OpenAlex API
authentication][upstream-source-3]

[upstream-source-1]: https://info.arxiv.org/help/api/user-manual.html
[upstream-source-2]: https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
[upstream-source-3]: https://help.openalex.org/api/authentication/
