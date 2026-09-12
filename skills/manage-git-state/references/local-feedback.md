# Mandatory local feedback

This suite requires commit-message, pre-commit, and pre-push validation for code
changes. Hooks complement required CI checks; they do not replace hosted
enforcement. Git hooks are local executable programs, not a security boundary.

## Apply the requirement within the authorized operation

Before committing, running a commit-producing integration, pushing, or preparing
a code PR/MR, inspect the repository's commit-message policy, existing hook
configuration, installation path, and CI task commands. The policy discovery
and default are defined in
[snapshots and refs](snapshots-and-refs.md). Reuse the project's hook manager,
message validator, and task runner. When a local
commit-creating or rewording operation is authorized and no manager exists, add
Lefthook and its reproducible installation through the repository's existing
toolchain; do not add a second manager. Authorization for that commit operation
includes this required repository-local gate. Do not proceed with the commit if
the gate cannot be installed without an unresolved ownership or policy
conflict.

A read-only review reports absent or ineffective hooks and proposes the missing
local checks; it does not install tools, edit configuration, or execute an
untrusted PR's hooks. Issue, release, ref-only, and settings operations that do
not create or reword commits do not require hook installation. Bisection
inspects current setup but must not install hooks into historical candidates or
alter the oracle. If a push needs missing setup outside the authorized scope,
report the gap and resolve that scope before proceeding; do not silently waive
the gate.

Inspect `git config --show-origin --get core.hooksPath` and existing executable
hooks before installation. An absent setting is normal. Preserve existing hooks
and manager integration; do not use installation options that force replacement
or reset `core.hooksPath`. Review new hook commands as executable code before
running them, especially in third-party repositories.

## Enforce the selected commit-message policy

Put message validation in the shared hook-manager configuration and install the
generated hooks before the first operation that can create or reword a commit.
Use the repository's configured validator and rules when present. If only a
documented custom style exists, select a maintained validator supported by the
repository's current toolchain and encode that style; do not replace it with
Conventional Commits. If neither policy nor validator exists, configure the
latest stable Conventional Commits rules with a maintained validator supported
by the current toolchain. Do not invent a partial regular-expression parser for
the specification.

Configure `commit-msg` to pass its message-file argument to the validator. Also
configure `applypatch-msg` with the same validator when the workflow permits
`git am`; do not assume a generated manager hook delegates to another hook.
Preserve legitimate policy-specific exceptions for generated merge, revert,
fixup, or squash messages only when the repository defines them. Do not add a
blanket skip for automation or integration operations.

With Lefthook, use `{1}` for the message-file argument, validate the
configuration, then run `lefthook install` so Git receives the generated hook
entry points. Use the repository's pinned invocation of Lefthook and its
validator rather than a global executable. Include hook installation in the
existing contributor setup and keep the configuration tracked; `.git/hooks`
alone is not reproducible.

## Share commands, not duplicate implementations

Map each reproducible CI gate to an existing local task with the same meaningful
flags, inputs, toolchain, and lockfile. Put quick non-mutating format/lint
checks and focused tests in pre-commit; put the broader local type-check, test,
and build gates in pre-push. CI must call the same underlying tasks and remain
the final gate for clean checkouts and contributors without installed hooks.

Do not run full model training, deployments, publication, destructive tests, or
secret-dependent production jobs in hooks. Use bounded fixtures, configuration
validation, and smoke tests locally; document which checks still require hosted
runners or long-running infrastructure and why. A smoke test is not evidence
that the full training run succeeds. Do not start an hours-long workload merely
to satisfy local/CI parity.

The following wiring example applies only when worktree inputs exactly match the
staged snapshot for commit, and a clean checkout matches the sole pushed HEAD
for push. It is not a general snapshot-isolating hook implementation. Outside
those conditions, require the snapshot-aware integration described below before
using it. The project must already define `just check-fast` and `just check`:

```yaml
pre-commit:
  commands:
    check-fast:
      run: just check-fast
pre-push:
  commands:
    check:
      run: just check
```

These task names are illustrative, not commands to invent in an existing
project. Prefer its current task runner; use just when new orchestration is
needed. Validate with `lefthook validate`, then use `lefthook install` only
after resolving existing hook ownership. Keep failures nonzero; do not use skip
flags, `--no-verify`, auto-staging, or a successful final command to hide
failure.

## Verify the snapshot and the actual Git gate

Worktree checks alone do not prove the staged snapshot passed. In particular,
`{staged_files}` selects names, not staged file contents. For partial staging,
use the existing manager's verified staged-content isolation, or test a
separately materialized index snapshot without changing the user's index or
worktree. Preserve unstaged edits and untracked files; reinspect both diffs
after hooks. Formatting should check, not silently rewrite or stage unrelated
work.

For pre-push, bind evidence to the local object IDs supplied to the hook, not
merely current HEAD or dirty worktree files. A push can update multiple refs or
push a commit other than HEAD. Validate each relevant pushed tip in an isolated
checkout when necessary; deletion-only updates need no code tests. Avoid adding
snapshot machinery where a clean checkout and a single HEAD push already match.

In a disposable repository with a local bare remote, prove that an invalid
message blocks commit creation, a valid policy-compliant message creates the
commit, a failing code check blocks commit creation, and a failing pre-push
check leaves the remote ref unchanged. If `applypatch-msg` is configured, prove
an invalid patch message is rejected through `git am`. Also prove passing paths
advance the intended refs. Exercise partial staging or non-HEAD pushes if the
configured integration claims to support them. A configuration parser or direct
validator/task invocation does not prove Git ran hooks.

## Sources

Verified 2026-09-13 with Lefthook 2.1.12, Conventional Commits 1.0.0, and Git
2.55.0 hook contracts:

- [Git hooks](https://git-scm.com/docs/githooks): executable hooks, installation
  paths, failure semantics, and pre-push object IDs on standard input.
- [Lefthook configuration](https://lefthook.dev/configuration/): supported
  configuration files; use one main configuration.
- [Lefthook run](https://lefthook.dev/configuration/run/): shell commands and
  file placeholders. File selection does not establish snapshot isolation.
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):
  current stable commit-message grammar and semantics.
