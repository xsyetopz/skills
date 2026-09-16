# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Build PCSX2 for the declared target, run the supplied test ELF with isolated
> settings, and investigate the GS dump mismatch.

Expected routing: `build-and-debug-pcsx2` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Build or debug DuckStation for PlayStation 1.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| PNACH generation | Distinguish generated patch syntax from executed guest behavior. | Patch construction reported as game verification. |
| Build/version mismatch | Use the exact revision documentation and CMake options. | Adjacent release instructions substituted. |
| User state | Keep test configuration and saves isolated. | Ordinary user data overwritten. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
