---
name: research-scientific-literature
description: >-
  Discover, verify, and synthesize primary scientific literature and
  contradictory evidence for an engineering or research decision. Not for
  routine API documentation.
---

# Research Scientific Literature

Search results are discovery metadata, not evidence that a paper establishes a
claim.

1. Restate the question, target system, decision, outcome, and applicability
   constraints. Expand acronyms, synonyms, adjacent fields, and contrary terms.
1. Run the [discovery CLI](scripts/discover_literature.py) with several queries.
   Use `--offline` only to reuse a populated cache. Deduplicate preprints,
   revisions, and published records before selecting papers.
1. Open each potentially decisive original paper independently. Identify the
   version read, method, workload or dataset, baselines, measured result, and
   limitations. Inspect supplements and linked code when the claim depends on
   them. Do not infer conclusions from title, abstract, citation count, venue,
   or discovery rank.
1. Search explicitly for replications, contradictory findings, later revisions,
   and follow-up work. Separate peer-review status from relevance and evidence
   quality.
1. Synthesize only supported claims. Prefer a compact table:

   | Work/version | Supported evidence | Limitation | Applicability |
   | --- | --- | --- | --- |

1. State the strongest supported conclusion, competing evidence, concrete
   engineering implication, remaining uncertainty, and the first measurement
   to run on the user's own workload.

The CLI queries keyless arXiv, Crossref, and OpenAlex routes, caches responses,
and emits normalized metadata. Its output never substitutes for reading a
paper. Read [discovery and evidence](references/discovery-and-evidence.md) for
source semantics, acquisition, and reporting rules.

## Validation

Trace every title, author, identifier, venue, and numerical claim to fetched
metadata or the paper itself. Link the exact paper version used. Label
unavailable full text and unresolved version linkage. Do not invent citations
or present a local benchmark as a scientific conclusion.

Run `python3 scripts/test_discover_literature.py` after changing the CLI.
