---
name: analyze-scientific-papers
description: >-
  Reads research papers critically, checking methods, statistics, and claims
  against evidence. Use when summarizing, reviewing, or comparing papers.
---

# Analyze Scientific Papers

Answer research questions from what the papers show: the exact version, the
table or section, and results whose statistics hold, scoped to the user's
setting.

## Rules

- Base conclusions on full text, code, or data, never on an abstract,
  metadata, citation count, or search rank; those only say what to read. If
  the decisive full text is unavailable, report the claim as unresolved and
  list what the full text would settle (tables, baselines, run counts).
- Pin the version: a DOI, or an arXiv ID with its `vN` suffix
  ([arXiv versions][versions]). A preprint and its published article can
  differ, and similar titles are different works.
- Before relying on a paper, look up corrections and retractions for its
  DOI: `curl -s 'https://api.crossref.org/works?filter=updates:DOI'` (Windows
  PowerShell 5.1: type `curl.exe`) ([Crossmark][crossmark]). Lead the
  summary with a retraction. A paper without a DOI needs its preprint
  server's version history instead.
- Cite a section, table, figure, or page for every finding, and separate
  what the authors claim from what their data show.
- Run `python3 scripts/check_stats.py FILE` on reported t, F, chi-square, z,
  and r results. A mismatch is a question for the authors (typo, one-tailed
  test, wrong df), not proof of misconduct
  ([statcheck][statcheck]).
- Report effect size, uncertainty, and n ("62% lower storage, n = 5 runs,
  range 55-70%"), not "significant": a p-value "does not measure the size
  of an effect or the importance of a result" ([ASA][asa]).
- Appraise the design before trusting a result: randomization, baselines
  tuned as much as the proposal, sample size, preregistration, data and
  code availability, overlap between evaluation and training data. Venue
  prestige does not replace these checks.
- Compare conflicting studies by design, population, and measure; never
  count significant against non-significant results, which the
  [Cochrane Handbook][cochrane] calls "unacceptable".
- Scope each conclusion to the paper's setting (population, scale,
  versions, hardware, date) and say where it may not transfer to the
  user's.
- Search at least two public providers, including one contrary-evidence
  query (replications, null results, critiques). Build queries from public
  terms only and ask before sending text from a private document. An
  empty result means this query on this index on this date found
  nothing; state providers,
  queries, and date in any "nobody has studied this" claim.
- Do not run a paper's code without reviewing it, and never invent a
  `mailto` or credentials for API calls.

## Scripts

- `python3 scripts/check_stats.py FILE|- [--json]` recomputes two-tailed
  p-values from APA-style t, F, chi-square, z, and r reports, allowing for
  rounding. Exit 0 consistent, 1 inconsistent, 2 unreadable input. It checks
  internal consistency only. On Windows, use `py -3` for `python3`.

## References

- Read [`references/search-and-identity.md`](references/search-and-identity.md)
  when searching arXiv, Crossref, or OpenAlex, or scripting queries.

[versions]: https://info.arxiv.org/help/versions.html
[crossmark]: https://www.crossref.org/documentation/crossmark/
[statcheck]: https://doi.org/10.3758/s13428-015-0664-2
[asa]: https://doi.org/10.1080/00031305.2016.1154108
[cochrane]: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-12
