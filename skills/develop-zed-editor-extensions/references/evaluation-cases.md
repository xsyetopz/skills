# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Implement this Zed extension using the target release APIs, language
> configuration, Tree-sitter queries, WASM constraints, LSP launch, tests, and
> packaging.

Expected routing: `develop-zed-editor-extensions` is selected because the
request requires its exact capability and domain procedure.

### Should not activate

> Change a normal Zed user setting.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Unsupported UI API | State the host limitation. | Invented manifest field or provider API. |
| Toolchain | Use the project-selected Rust toolchain. | Stable channel forced silently. |
| Downloaded binary | Verify platform, integrity, permissions, and lifecycle. | Unverified executable launched. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
