---
name: analyze-scientific-papers
description: >-
  Finds, reads, and weighs scientific papers for a research question, checking
  versions, retractions, and reported statistics. Use when asked what the
  literature says or whether a paper's claims hold. Not for citation
  formatting.
---

# Analyze Scientific Papers

Answer research questions from what papers show: the exact version, the
section or table, and statistically consistent results, scoped to the
user's setting.

## Workflow

1. Write the question as a claim with a scope, for example "X reduces Y
   by ≥ Z in setting S" ([applicability][apply]).
1. Search at least two providers with native queries. Record each
   provider, query, date, and filter ([search][search]). Then run a
   disconfirming query ([contrary][contrary]).
1. For each candidate paper, pin its version (DOI, or arXiv `vN`) and
   look up its corrections and retractions ([identity][identity],
   [updates][updates]).
1. Read the full text of every paper the answer depends on. Record the
   section, table, or figure in an evidence note
   ([evidence level][level], [location][location]).
1. Run `check_stats.py` on the quoted results. Appraise the design,
   and record effect sizes with their uncertainty ([stats][stats],
   [design][design], [effect][effect]).
1. Synthesize across studies by comparing designs, not by counting
   significant results ([conflicts][conflicts]).
1. Run `check_evidence_note.py` on every note. Answer with scoped
   conclusions, each linked to its notes, and list what was not read or
   not searched.

## Route the task to a card

| Task | Card |
| --- | --- |
| Find papers on a question | [Provider and native query][search] |
| Which version is this? | [Version identity][identity] |
| Avoid one-sided results | [Disconfirming search][contrary] |
| Is it retracted or corrected? | [Corrections and retractions][updates] |
| Scripted or bulk queries | [Rate limits][rates] |
| "Nobody has studied this" | [Zero results][zero] |
| Can I cite this abstract? | [Evidence level][level] |
| Summarizing findings | [Claim to location][location], [effect size][effect] |
| Do the numbers add up? | [Statistical consistency][stats] |
| Is the study sound? | [Design appraisal][design] |
| Papers disagree | [Conflicting studies][conflicts] |
| Does it apply to us? | [Applicability][apply] |

## Rules

- Conclusions rest on full text, or on code and data, never on
  metadata, abstracts, citation counts, or search rank.
- Every source has a DOI, or an arXiv ID with its version. Every
  finding names a section, table, figure, or page.
- Report effect sizes with uncertainty and n. "Significant" alone is
  not a finding.
- Absence claims name the providers, queries, and date searched.
- Do not run code from a paper without reviewing it. Never infer a
  `mailto` or credentials.

## Bundled tools

- `scripts/fetch_metadata.py --provider arxiv|crossref|openalex
  (--query Q | --id ID) [--param K=V] [--limit N] [--output FILE]`
  queries one provider natively per call and returns the native
  response, with bounded retries. Tested by
  `scripts/test_fetch_metadata.py`.
- `scripts/check_stats.py FILE|-` recomputes p-values from t, F, χ², z,
  and r reports.
- `scripts/check_evidence_note.py NOTE.md...` checks evidence notes
  against the template's rules and refuses "supported" when only an
  abstract was read.
- `scripts/test_analysis_tools.py` tests the two checkers.
- `assets/evidence-note-template.md`;
  `assets/examples/{note-supported.md, note-abstract-only.md,
  results-section.txt}`; `assets/metadata-fixtures/`.
- `sh assets/examples/verify.sh [network]`: offline by default;
  `network` adds live, read-only metadata queries.

## References

- [Search and identity](references/search-and-identity.md)
- [Reading and synthesis](references/reading-and-synthesis.md)

## Completion evidence

- The searches run: provider, query, date, and filters, including the
  disconfirming query.
- The evidence notes, with `check_evidence_note.py` passing, and the
  corrections lookup for each source.
- The `check_stats.py` output for the quoted statistics.
- Scoped conclusions: supported, contradicted, or unresolved, each
  linked to its notes.
- What was not read, not searched, or not accessible (for example,
  paywalled full text).

## Stop and ask

- The decisive paper's full text is not accessible, and the conclusion
  would rest on its abstract.
- The question's scope (population, setting, date) is too vague to
  judge whether a finding applies.
- A paper's code would need to run with side effects or credentials.

[search]: references/search-and-identity.md#provider-and-native-query
[identity]: references/search-and-identity.md#version-identity
[contrary]: references/search-and-identity.md#disconfirming-search
[updates]: references/search-and-identity.md#corrections-and-retractions-lookup
[rates]: references/search-and-identity.md#rate-limits-and-credentials
[zero]: references/search-and-identity.md#zero-results-are-not-absence
[level]: references/reading-and-synthesis.md#evidence-level
[location]: references/reading-and-synthesis.md#claim-to-location
[stats]: references/reading-and-synthesis.md#statistical-consistency-check
[effect]: references/reading-and-synthesis.md#effect-size-and-uncertainty-over-significance
[design]: references/reading-and-synthesis.md#study-design-appraisal
[conflicts]: references/reading-and-synthesis.md#conflicting-studies-without-vote-counting
[apply]: references/reading-and-synthesis.md#applicability-to-the-question
