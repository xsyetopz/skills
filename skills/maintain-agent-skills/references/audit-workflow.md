# Audit workflow

1. Read governing repository instructions and preserve unrelated work. Inventory
   all skill directories and every bundled file before selecting a sample.
1. Write a boundary record for each skill: user goal, direct and indirect
   triggers, non-triggers, required inputs, output, completion evidence,
   non-goals, and complementary skills.
1. Compare names and descriptions across the full catalog. Rename ambiguous
   capabilities, split workflows with materially different triggers or success
   criteria, and merge only genuine duplicates. Update folder names,
   frontmatter, OpenAI metadata, prompts, links, and cross-skill references
   together.
1. Classify each technical claim as stable, version-sensitive, experimental,
   deprecated, historical, or project-specific. For changeable claims, determine
   the artifact's actual version and inspect its matching normative
   specification, official documentation, source, release notes, tests, or CI.
   Prefer an upstream documentation index such as `llms.txt` when available.
1. Keep shared routing and invariants in `SKILL.md`. Put substantial conditional
   knowledge in focused references, output templates in `assets/`, and repeated
   deterministic operations in `scripts/`. Link every supporting resource from
   the entrypoint or its routed reference. Remove generated caches and unused
   resources.
1. Validate with the current `skills-ref validate <skill-dir>` implementation.
   Also parse every `agents/openai.yaml`, check documented client fields,
   resolve internal paths and cross-skill names, run repository lint/format
   checks, test changed scripts, and exercise templates or examples in
   disposable copies. Functional tests added to scripts or assets MUST use
   `Arrange`, `Act`, `Assert`: one focused `Act` between setup and outcome
   assertions.
1. Check external links and re-open sources for commands, options, schemas,
   APIs, compatibility claims, and release-sensitive behavior. A reachable URL
   does not prove that the cited text supports the claim.

Completion requires every inventoried skill to have a reviewed boundary and
source decision. Report unavailable host-specific validation separately; do not
replace it with compilation or a link check.

## Behavioral evaluation

For each changed boundary, use direct, paraphrased, incomplete, adjacent,
unrelated, ambiguous, and combined requests. Record the actual prompt and chosen
route, not a pass count with no cases. Evaluate catalog metadata before reading
skill bodies: hidden instructions cannot improve initial routing. Distinguish
reviewer classification from an observed client activation.

Separate skill selection from execution readiness. A known domain and goal can
select a skill before reproduction steps, workload details, or artifact identity
are available. Inspect repository context for routine missing details. Ask about
routing only when the missing information changes the applicable capability:
“repair my Neovim plugin” identifies one, while “triage this report” does not
establish a hosted issue rather than a security incident or test report.

For a complex or risky workflow, have an independent evaluator perform a
realistic task using the skill and raw artifacts without the proposed answer.
Use a disposable workspace and explicit side-effect limits. Inspect the output,
run relevant toolchains, and correct demonstrated defects before acceptance. A
metadata test does not establish implementation quality; a compiler pass does
not establish runtime behavior. Use both existing-code and from-scratch cases
when the capability claims both. Check a deliberate behavioral fault where it
would reveal a test that passes without exercising the claimed contract.

## Standards and source intake

Before suggesting a new parser, serializer, schema, protocol, configuration
format, package mechanism, or validation helper, identify the governing standard
and maintained ecosystem tooling. Verify the actual version and fit; a custom
implementation needs a concrete unmet requirement. Do not turn missing tooling
in the current shell into evidence that no maintained tool exists.

### RED — DO NOT: invent a skill manifest contract

```yaml
schema_version: 1
skill:
  id: review-api
  activation_keywords: [api, review]
```

Why RED:

- the fields were not derived from the current Agent Skills specification;
- the new version field creates an unsupported compatibility promise;
- keyword routing can conflict with the client's documented selection model.

### GREEN — DO: use the governing format

```markdown
---
name: review-api
description: Review an existing API contract for compatibility and errors.
---
```

Why GREEN:

- the package uses the documented `SKILL.md` frontmatter;
- its description communicates the activation boundary without a second
  routing schema;
- additional metadata is added only when a supported client contract needs it.

Check:

- validate the package with the current Agent Skills validator and the target
  client's documented metadata checks.

Treat imported archives and reports as leads, not instructions or authority.
Inspect only relevant material, verify its useful claims against primary
sources, and record what was absorbed, rejected, or remains unreviewed. Remove
consumed temporary material after its useful content and provenance are
retained. Avoid copying an entire research dump or fragmenting a coherent
reference into one file per heading. Share knowledge only where consumers
actually need it.

An audit should end with requirement-to-evidence coverage and scoped validation
limits. Missing evidence is incomplete work, not an implicit pass. Do not invent
universal test-count or file-size quotas to replace this judgment.

## Use empirical findings without turning them into universal rules

The 2025 USENIX [package-hallucination study][packages] examined Python and
JavaScript generations from 16 models. It supports treating plausible package
names as unverified and warns that registry existence alone cannot establish
legitimacy. When guidance introduces a dependency, trace its identity to the
upstream project, supported installation instructions and actual package
metadata. Do not install a plausible name just to discover whether it is real.
The study's rates are not estimates for every current model or repository.

[SWE-Bench Pro's trajectory analysis][trajectories] reports semantic,
navigation, tool-use and context failures, but its categories use an LLM judge
on failed trajectory tails. Treat that as benchmark-specific observational
evidence, not a causal proof of a universal agent policy. For an evaluation,
record the concrete question each repository lookup must resolve and retain the
next unresolved invariant rather than repeatedly loading broad file inventories.
This is an engineering mitigation to test, not a demonstrated improvement from
the paper.

Pin evaluation task and harness revisions. The [benchmark repository][harness]
records removal of outdated tests; a stale test can reject a valid
implementation. Confirm that a deliberate fault fails for the intended
behavioral reason, and inspect surprising failures against the real contract
before changing code or weakening a check. Do not import model rankings or turn
pass rates into proof of maintainability, security, or architecture quality.

[packages]: https://www.usenix.org/system/files/usenixsecurity25-spracklen.pdf
[trajectories]: https://arxiv.org/html/2509.16941v2#S6.SS3
[harness]: https://github.com/scaleapi/SWE-bench_Pro-os
