# Local Git feedback and bounded CI logs

Date: 2026-09-12. User-requested addition after the whole-suite audit: mandatory
local pre-commit/pre-push checks and no repeated retrieval of huge CI logs.

## Implemented contracts

- Git state owns [mandatory local feedback][feedback]. Hosted code PR/MR work,
  CI pipeline work, and bisection route to that shared policy rather than copy
  it. Bisection and read-only reviews inspect/report; they do not install hooks
  or modify historical candidates. Unrelated issue/settings work is excluded.
- Existing hook managers and task runners take precedence. Lefthook is the
  default only for authorized setup without an existing manager. Existing
  executable hooks and `core.hooksPath` must be preserved. Installation alone is
  not validation, and a local gate does not replace required hosted checks.
- Local tasks reuse reproducible CI commands. Fast checks run before commit;
  broader checks run before push. Long training, deployments and
  secret-dependent jobs remain explicit exceptions, with bounded local
  smoke/configuration checks and no claim that those prove a full training run.
- [CI evidence][logs] requires exact run/attempt/job/head identity, successful
  task-local caching, bounded excerpts, and local reuse. Filtered CLI output is
  not assumed to bound network downloads. No repeated full-run logs, unapproved
  external log uploads, automatic reruns, or tight status polling.

## Independent scenario review

A reviewer applied the new routes to five scenarios: read-only failed training
PR, partial staging with an existing manager, new local/CI setup, historical
bisection, and non-HEAD push. The log-reuse and authorization actions matched
the policy. Two example-scope findings were accepted: the minimal hook wiring
now explicitly requires matching worktree/index inputs and a clean single-HEAD
push, rather than implying automatic snapshot isolation.

A reported missing privileged-CI trust boundary was rejected after reading the
already-required provider references. `provider-behavior.md` prohibits executing
untrusted checkouts/artifacts in privileged workflows and restricts deployment
credentials and OIDC; `github-actions.md` covers contributor execution, source
run validation, environment approval, and ref/audience restrictions. The
reviewer had not been given those deep references. No duplicate policy was
added.

## Real executable evidence

Installed Lefthook 2.1.12 validated and installed the documented configuration
in an isolated repository. Existing just was used for the two check tasks. The
remote was a disposable local bare repository; no external push occurred.
Harness and full command output are under `/tmp/skills-hook-evidence/`.

Five outcome checks passed:

1. A failing pre-commit task returned failure, left HEAD unchanged, and
   preserved the staged failing blob.
2. A passing worktree task with failing staged content demonstrated the
   partial-staging false positive. Materializing the index into a separate
   directory and running the same task failed, preserving both index and
   worktree content. The minimal Lefthook example does not claim automatic
   staged-content isolation.
3. A failing broader pre-push task rejected a real Git push and left the bare
   remote's main ref unchanged.
4. Passing commit/push paths advanced the intended local and remote refs.
5. Normal Lefthook installation refused an existing configured `core.hooksPath`;
   its value and existing executable hook bytes were unchanged. No force/reset
   options were used.

Installed `gh run view --help` and its official manual confirmed the documented
attempt/job selectors, failed-step log option, and archive fallback limitation.
No live hosted run was fetched: download size, provider caching, and network
failure behavior were not empirically tested. Non-HEAD/multiple-ref pushes are
covered by the required snapshot contract, not claimed as tested by this simple
clean-HEAD fixture. No hooks were installed in the skills repository.

[feedback]: ../skills/manage-git-state/references/local-feedback.md
[logs]: ../skills/manage-hosted-repositories/references/ci-evidence.md
