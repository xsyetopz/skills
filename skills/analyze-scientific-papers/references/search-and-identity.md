# Search and identity

Finding papers and pinning each to the exact version meant. The tool is
`scripts/fetch_metadata.py`: one provider per call, with the native
response kept as received.
`assets/examples/verify.sh network` ran live, read-only queries against
arXiv, OpenAlex, and Crossref on 2026-09-25.

## Contents

- Provider and native query
- Version identity
- Disconfirming search
- Corrections and retractions lookup
- Rate limits and credentials
- Zero results are not absence

## Provider and native query

**Definition.** Each index has its own coverage and query syntax:

- **arXiv:** preprints, searched with field syntax such as
  `all:"tail sampling"` ([arXiv API][arxiv]).
- **Crossref:** DOI metadata from publishers, with `filter=`
  parameters ([Crossref REST][crossref]).
- **OpenAlex:** works, citations, and filters such as
  `from_publication_date:` ([OpenAlex][openalex]).

`fetch_metadata.py` sends one native query and passes other native
options through `--param`.

**Use when.** Looking for papers on a question, or confirming that a
cited paper exists.

**Do not use when.** Never treat any index as complete. Record which
providers you did not search.

**Example.**

```sh
python3 scripts/fetch_metadata.py --provider arxiv \
  --query 'all:"tail sampling"' --limit 3 --output arxiv.atom
python3 scripts/fetch_metadata.py --provider openalex \
  --query 'distributed tracing tail sampling' \
  --param 'filter=from_publication_date:2020-01-01' --limit 8
```

Live results on 2026-09-25: 3 arXiv entries and 3 OpenAlex results.

**Cost removed.** Searches that quietly cover one index, and merged
records that mix up different works.

**Verify.**

1. The evidence note's `Search:` field records the provider, the exact
   query, the date, the filters, and the providers not searched.

## Version identity

**Definition.** Each arXiv version has an ID with a `vN` suffix
([versions][versions]). A DOI names a published version. A preprint
and the published article can differ, even when they are linked.

**Use when.** Citing or quoting any result.

**Do not use when.** Never match on title alone. Similar titles with
different authors, venues, or years are different works.

**Example.** Fetch an exact arXiv version with
`--provider arxiv --id 2303.08774v6`. The tool keeps the suffix.

**Cost removed.** Quoting a number that changed between v1 and v3.

**Verify.**

1. The note's `Source:` field carries the DOI, or the arXiv ID with its
   `vN`. `check_evidence_note.py` rejects a source without one.

## Disconfirming search

**Definition.** A second query that looks for evidence against the
claim: failed replications, null results, critiques, and limitations.
Synonyms of the first query do not count.

**Use when.** Any question where a finding might not generalize.

**Do not use when.** Never stop after the first supportive paper.

**Example.**

```sh
python3 scripts/fetch_metadata.py --provider openalex \
  --query 'tail sampling overhead limitations replication' --limit 8
```

**Cost removed.** One-sided summaries, visible as a note that considers
no contrary results.

**Verify.**

1. The note lists the disconfirming query and what it found, including
   "nothing relevant".

## Corrections and retractions lookup

**Definition.** Crossref's `filter=updates:DOI` returns notices that
update a work, such as corrections and retractions. Their `update-to`
entries give the notice type, and some come from Retraction Watch
([Crossmark][crossmark]).

**Use when.** Every paper the conclusion relies on.

**Do not use when.** The work has no DOI. Check the preprint server's
version history instead.

**Example.** Executed for the 1998 Lancet paper
10.1016/S0140-6736(97)11096-0:

```sh
python3 scripts/fetch_metadata.py --provider crossref --query retraction \
  --param 'filter=updates:10.1016/S0140-6736(97)11096-0' --limit 5
```

Result: two notices, of types `correction` (2004) and `retraction`
(2010).

**Cost removed.** Relying on retracted results, at the cost of one query
per paper.

**Verify.**

1. The note's `Updates:` field records the lookup and its date.

## Rate limits and credentials

**Definition.** The providers limit request rates:

- arXiv asks for at least 3 seconds between requests;
- Crossref's polite pool uses a `mailto` that you pass explicitly;
- OpenAlex takes an optional API key in an Authorization header.

`fetch_metadata.py` honors `Retry-After`, refuses redirects, and caps
responses at 16 MiB.

**Use when.** Scripting several queries.

**Do not use when.** Never guess the user's email for `mailto`; pass it
only when the user supplied it.

**Example.** `verify.sh` runs `sleep 3` between the arXiv query and the
next request.

**Cost removed.** Blocked IPs, and responses silently cut short.

**Verify.**

1. `python3 scripts/test_fetch_metadata.py` passes (12 tests, offline,
   with the fixtures in `assets/metadata-fixtures/`).

## Zero results are not absence

**Definition.** An empty result means this query, on this index, on this
date, returned nothing, not that no such work exists.

**Use when.** Reporting that something "has not been studied".

**Do not use when.** Never state absence without at least two providers
and varied terms.

**Example.** Report it as: "No results for query X on Crossref and
OpenAlex on 2026-09-25; arXiv not searched."

**Cost removed.** False claims of novelty or of missing evidence.

**Verify.**

1. Every absence claim names the providers, the queries, and the date.

[arxiv]: https://info.arxiv.org/help/api/user-manual.html
[crossref]: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
[openalex]: https://docs.openalex.org/
[versions]: https://info.arxiv.org/help/versions.html
[crossmark]: https://www.crossref.org/documentation/crossmark/
