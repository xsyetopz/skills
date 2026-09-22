---
name: analyze-scientific-papers
description: >-
  Use when finding, reading, comparing, or synthesizing scientific papers for a
  research question, including methods, results, replications, corrections, and
  limitations. Not for citation formatting alone or conclusions drawn only from
  search metadata.
---

# Analyze Scientific Papers

Answer a defined research question from inspectable primary evidence. Separate
discovery metadata, paper content, reported results, and your synthesis so an
inaccessible method or missing dataset is not filled from model memory.

## Operating contract

- Treat the research question, inclusion criteria, population, intervention or
  exposure, outcomes, and time period as the scope boundary.
- Use metadata services to discover papers; use the paper, supplement, registry,
  correction, or data repository to support substantive claims.
- Preserve study design and uncertainty. Association is not causation,
  statistical significance is not practical importance, and absence of evidence
  is not evidence of absence.
- Do not fabricate inaccessible methods, sample sizes, effect estimates,
  quotations, DOI records, or replication status.
- Handle paywalled or unavailable material as an explicit evidence gap. Do not
  substitute a neighboring paper or review without labeling it.

## Evidence-handling contract

- Treat the user goal, scope, approval boundary, and required evidence as
  controlling. This skill narrows how to produce a paper synthesis; it MUST NOT
  broaden authority or override repository instructions.
- For GPT-5.6 and GPT-6, provide scientific claims, study methods, and source
  provenance, hard constraints, available tools, and the finish condition once.
  Remove repeated directions and examples unless a recorded evaluation shows
  that they prevent a real failure.
- Infer routine, reversible steps from inspected evidence. Ask only when an
  unresolved choice changes an external contract. Stop before an external write,
  destructive action, credential use, or material scope expansion that the user
  did not authorize.
- Load a linked reference only when its subject affects the current decision.
  Use scripts for deterministic mechanics; use model judgment for semantic
  decisions. Inspect tool output before relying on it.
- Validate at the boundary of the claim with claim-to-source checks, correction
  searches, and design-specific appraisal. Report commands, observed results,
  and gaps. A parser, build, or single green test proves only the property that
  it can discriminate.
- Use **MUST** only for an absolute safety or interoperability requirement,
  **SHOULD** for a default with valid exceptions, and **MAY** for an option.
  Write short active sentences and use one stable term for each concept. This
  style is STE-inspired; it is not a claim of formal ASD-STE100 conformance.

## Workflow

```mermaid
flowchart LR
    Q[Research question] --> P[Protocol and inclusion rules]
    P --> D[Database and citation discovery]
    D --> S[Screen title and abstract]
    S --> F[Read full text and supplements]
    F --> E[Extract methods and results]
    E --> C[Compare studies and assess limitations]
    C --> Y[Synthesis with scoped claims]
    F -->|Unavailable| G[Record evidence gap]
```

## Procedure

1. Operationalize the question before searching. Record the target population or
   system, intervention/exposure, comparator, outcomes, eligible designs, date
   range, and exclusions that materially affect the answer.
1. Search more than one appropriate index when coverage matters. Use stable
   identifiers such as DOI, PMID, arXiv ID, trial registration, or repository
   accession to de-duplicate records. Save exact queries and search dates for
   reproducibility.
1. Screen against the stated criteria. Exclude with a reason rather than
   silently dropping inconvenient or contradictory results. Follow citations,
   corrections, retractions, protocols, and companion papers when they change
   interpretation.
1. Read the full methods and results for load-bearing claims. Extract sample
   construction, controls, measurement, missing-data handling, statistical
   model, uncertainty, effect size, subgroup definition, and deviations from
   preregistration where available.
1. Compare studies on design and applicability before combining conclusions. Do
   not average incomparable outcomes or transfer results between populations,
   versions, doses, environments, or endpoints without a defensible mapping.
1. Synthesize by claim. State which studies support or conflict, the strongest
   limitations, and what remains unknown. Prefer exact estimates with
   uncertainty over vote counting by significance.
1. Return citations adjacent to the claims they support. Distinguish
   paper-reported facts, your inference, and recommendations. Include the search
   and access limits when they could change the conclusion.

## Choose the next research reference

| Situation | Read or use |
| --- | --- |
| Designing a search, de-duplicating records, or separating metadata from evidence | [Discovery and evidence boundaries](references/discovery-and-evidence.md) |
| Choosing review scope, inclusion rules, and synthesis method | [Study selection and synthesis rules](references/scientific-literature-study-selection-and-synthesis-rules.md) |
| Extracting methods and comparing claims | [Worked evidence-extraction examples](references/scientific-literature-paper-synthesis-case-studies.md) |
| Judging what a source or analysis actually establishes | [Claim-to-source verification](references/scientific-literature-claim-to-source-verification.md) |
| Handling inaccessible papers, conflicting studies, or weak designs | [Literature-review biases and recovery](references/scientific-literature-literature-review-biases-and-recovery.md) |
| Using the bundled metadata retriever | [Metadata retrieval helper](scripts/fetch_metadata.py) |
| Preparing a structured research note | [Evidence note template](assets/evidence-note-template.md) |
| Checking official APIs and source freshness | [Scholarly data and method authorities](references/scientific-literature-scholarly-data-and-method-authorities.md) |

## Research decision references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Claims, methods, and applicability](references/scientific-literature-claims-methods-and-applicability.md) | Use when distinguishing the requested paper synthesis from observed repository state. |
| [Enterprise operation and governance](references/scientific-literature-research-provenance-and-governance.md) | Use when the paper synthesis crosses ownership, data-handling, release, or audit boundaries. |
| [Review tools and output templates](references/scientific-literature-review-tools-and-output-templates.md) | Use when locating bundled resources for the paper synthesis. |

## Behavioral evaluation

Run [the maintained Agent Skills evaluations](evals/evals.json) in clean
target-client contexts. Compare this revision with a no-skill or prior-skill
baseline. Review commands, diffs, and artifacts; do not grade prose alone. The
checked-in cases are test inputs, not claimed results.

## Bundled executable helpers

- `scripts/fetch_metadata.py --help`
- `scripts/test_fetch_metadata.py`

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- `assets/evidence-note-template.md`

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Exact research question and selection criteria.
- Search sources, exact queries, dates, and screening limits.
- Per-study evidence with stable identifiers, design, population, methods,
  results, uncertainty, and limitations.
- Claim-level synthesis that identifies agreement, conflict, applicability, and
  unknowns.
- Citations to the actual paper or authoritative record supporting each material
  claim.

## Stop or escalate

- The question requires a material population, outcome, or policy choice that
  the user has not defined and source inspection cannot resolve.
- The load-bearing full text or data is unavailable; report the narrower
  evidence instead of reconstructing it.
- The available studies are not comparable enough for the requested aggregate
  conclusion.
- The request would require overstating causality, clinical applicability, or
  current consensus beyond the evidence.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
