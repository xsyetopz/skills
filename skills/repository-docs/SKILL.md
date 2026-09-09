---
name: repository-docs
description:
  Write or audit README, changelog, release notes, contribution guides,
  templates, or repository governance from project evidence. Excludes AGENTS.md
  and runtime implementation.
---

# Repository Docs

Derive document claims from manifests, source, CI, release refs, and enforced
policy. Correct unsupported claims and nonstandard formats in the requested
documents.

- `CHANGELOG.md`: use Keep a Changelog 1.1.0, including when rewriting an
  existing changelog. Keep release facts and history accurate.
- Release versions: apply SemVer 2.0.0 to the declared public API. Do not
  renumber published releases.
- CODEOWNERS and templates: use the hosting provider's native syntax and
  locations.
- README and CONTRIBUTING: document executable setup, expected results,
  contribution checks, and applicable policy. These files have no universal
  schema.

Read [formats and governance][ref-1] for procedures, examples, provider
differences, and validator contracts. Use the
[changelog validator](scripts/audit_changelog.py) for changelog edits and the
[SemVer validator](scripts/audit_semver.py) for version checks.

Validate changed links, paths, commands, and claims. Run checks relevant to the
changed document. Report unresolved factual or policy decisions precisely.

[ref-1]: references/formats-and-governance.md
