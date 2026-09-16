# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Implement this VS Code extension feature for desktop and remote hosts with
> URI-safe access, cancellation, document version checks, Workspace Trust,
> tests, and VSIX inspection.

Expected routing: `develop-vscode-extensions` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Create a Visual Studio IDE extension.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Remote URI | Use workspace/file-system APIs, not local path assumptions. | Remote host broken by fs path use. |
| Stale async result | Check URI and version before publishing. | Old result changes current document. |
| Trust | Do not execute workspace content before trust permits it. | Untrusted repository gains execution. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
