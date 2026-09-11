# Security and testing capability evaluation

Date: 2026-09-11. These evaluations cover the two new skills, not the full
suite.

## Boundary decisions

The prior 38-skill catalog had architecture, domain-specific performance and
extension workflows, and hosted-operation skills. It had no reusable defensive
security-review or behavioral-test design workflow. Adding generic “best
practices” to every entrypoint would dilute activation and duplicate guidance.

- `review-software-security` owns threat models, reachable vulnerability review,
  and security-fix evidence. Design and code review share actors, boundaries,
  threat reasoning, and the finding/verification output. Offensive live-system
  work, incident response, and compliance certification are excluded.
- `test-software-behavior` owns test design/implementation, regression evidence,
  and flaky-test diagnosis. Test techniques remain conditional references rather
  than separate unit/property/fuzz/contract micro-skills. Routine test
  execution, CI configuration, and performance optimization are excluded.

The skills compose when a confirmed security failure needs regression coverage.
Neither should activate on every normal implementation task.

## Catalog-only routing

An independent test-engineer read only all 40 name/description frontmatters, not
skill bodies, fixtures, audit notes, or expected answers. Actual selections:

1. API cross-tenant review and fix verification: security review.
2. Low-privilege export-worker disclosure: security review.
3. Threat model without deployment/identity details: security review, unresolved
   inputs identified.
4. Require two GitHub branch approvals: hosted-repository configuration.
5. Rename one UI label, no other changes: no skill.
6. “Is this parser safe?”: clarify the safety property before selecting a skill.
7. Upload threat model plus authorization regressions: security and testing.
8. Tests for file-truncation regression and old behavior: testing.
9. Browser suite flaky only in parallel CI: testing, not pipeline migration.
10. Better tests with only a feature description: testing, identify missing
    acceptance criteria.
11. Move unchanged test job to GitLab CI: CI pipelines, not testing.
12. Run an existing test command and report its status: no skill.
13. “Verify this release”: hosted-release workflow was selected provisionally;
    provider and verification scope were identified as unknown. This remains a
    case to check in the hosted-release boundary audit, not proof of its
    routing.
14. Move storage out of UI and test transactions: architecture plus testing.

Unselected routine execution/implementation tasks do not justify adding generic
micro-skills. No new skill was added for every gap named by an evaluator.

## Security forward test

An independent cyber-defender used the security skill on a synthetic SQLite
report service. The user contract established authenticated principals,
per-tenant export authorization, no database row-level policy, and no production
targets. The fixture had a parameter-bound query by report ID, but omitted the
principal's organization in the export query. Its list operation did filter by
organization. The evaluator was not told the defect or expected answer.

The evaluator produced two real unittest cases: an own-organization export
passed; a cross-organization export failed because it disclosed the synthetic
bytes. It proposed constraining the authoritative query by both report and
organization IDs, and did not misclassify parameter binding as SQL injection.
HTTP middleware, headers, caches, and deployment controls were correctly
reported as unknown.

The coordinator inspected the tests and applied only the proposed query change
in a disposable copy: both cases passed. The original fixture remained
unchanged. Qualitative severity was explicitly not a CVSS or project-defined
score.

Artifacts were isolated under `/tmp/skill-security-forward`, not shipped as
skill assets. Input `reports.py` SHA-256:

```text
0a589083c3b7ab4753dd1fb3eeb0728f64003e265055a8f5e59459023ce3fb58
```

## Testing forward test

An independent test-engineer used the testing skill against a disposable copy of
the repository's real SemVer CLI and its documented narrow extraction contract.
It did not read the existing tests, prior diffs, or known defects. The request
was tests-only, using unittest, with proof against plausible faulty variants.

The evaluator produced six tests covering direct validity and order, text/JSON
status agreement, tag wrappers/filtering, changelog selection/order, bad
arguments, and unreadable sources. All six passed with Git available. Three
isolated mutations changed tag-wrapper acceptance, Unreleased exclusion, and
direct-input order; the tests rejected all three.

Integration review found that the initial mutation runner accepted any nonzero
exit rather than checking an assertion failure, and one missing-file fixture
used a shared fixed temporary path. Those are evidence-quality defects, not
production bugs. The evaluator repaired both, removed a redundant order
assertion, and ran Ruff lint/format checks without suppressions. The corrected
runner requires the named test's expected assertion failure, no setup errors or
skips, and an unchanged original script. The coordinator inspected those
corrections. Final results:

```text
Ran 6 tests ... OK
detected tag-wrapper via 1 != 0
detected unreleased-heading via 'Unreleased'
detected direct-order via '1.5.0'
```

The skill already states fixture-isolation and failure-classification
requirements; the misses did not justify adding duplicate instructions. This
follow-up is an integration correction, not a fresh blinded trial.

Artifacts are under `/tmp/skill-testing-forward`. The production script was not
changed. Input `audit_semver.py` SHA-256:

```text
02a0563bd89e3a4681f055c38b2109c5d782d0e6beb89dc185f2f68ee925833b
```

## Source verification and limitations

New references synthesize current OWASP guidance, published ASVS 5.0.0, IETF
OAuth and JWT BCPs, NIST's final/draft SSDF distinction, SLSA 1.2, and official
testing tool documentation. URLs and claim-specific provenance are adjacent in
the skills. The USENIX Security 2025 package-hallucination paper supports
dependency-identity verification; its measured rates were not generalized to
current models.

The verification/security sections of the supplied agent-failure notes informed
scope-matched evidence and tool-authority guidance. Their broad source links do
not prove every listed behavior is empirically recurrent. Those mitigations are
engineering recommendations, with separate primary support where available. The
notes remain partially unconsumed and have not been deleted.

Both new skills pass `skills-ref`, bundled `quick_validate.py`, Markdown lint,
and Ruff Markdown formatting. Generated OpenAI metadata follows the bundled
generator; the skills have no external tool dependency or explicit-only
invocation policy.

These are limited forward tests, not exhaustive security/test-technique
validation. No live service, native sanitizer, fuzz engine, browser, or
package-install test was run for these skills. They contain decision guidance
rather than executable starter assets. The full GOAL.md acceptance audit remains
incomplete.
