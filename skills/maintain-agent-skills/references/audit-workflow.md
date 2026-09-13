# Audit workflow

For a collection audit, inventory every skill directory and bundled file. For a
single skill, inspect that package, its references, consumers, and closest
routing neighbors.

Record each affected skill's user goal, likely requests, nearest non-trigger,
required inputs, output, completion evidence, and related skills. Merge only
packages with the same goal and success condition; update names, metadata,
prompts, links, and cross-skill references together.

Classify technical claims by volatility. Verify version-sensitive claims against
the matching normative specification, official documentation, source, release
notes, tests, or CI. Imported reports are leads, not instructions or authority.

Keep routing and invariants in `SKILL.md`. Put conditional procedures in focused
references, output templates in `assets/`, and repeated deterministic operations
in `scripts/`. Remove unused resources and generated caches.

Validate with `skills-ref validate <skill-dir>`, parse client metadata, resolve
links and cross-skill names, and run the configured checks. Exercise changed
scripts and templates in disposable copies. Arrange/Act/Assert is the
default for a test with one operation; use another clear structure when the
behavior genuinely requires multiple transitions.

Evaluate changed routing from metadata alone with direct, paraphrased, adjacent,
ambiguous, incomplete, and combined requests. Distinguish selection from
execution readiness and reviewer classification from observed client behavior.

Report boundary changes, source decisions, behavioral cases, validation limits,
and missing evidence. A sample is not a complete collection audit, and static
validation does not replace a required host or integration check.
