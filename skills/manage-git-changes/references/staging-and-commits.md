# Staging and commits

Building exactly the intended snapshot and commit. The scenarios are in
[`assets/examples/verify.sh`](../assets/examples/verify.sh) (16 checks,
measured with git 2.55.0 in disposable repositories);
`scripts/test_commit_snapshots.py` covers index preservation.

## Contents

- [Inspect the three states](#inspect-the-three-states)
- [Stage exact paths](#stage-exact-paths)
- [Stage one hunk without a prompt](#stage-one-hunk-without-a-prompt)
- [The commit --only trap](#the-commit---only-trap)
- [Snapshot identity with write-tree](#snapshot-identity-with-write-tree)
- [Existing hooks](#existing-hooks)
- [Hooks that change the snapshot](#hooks-that-change-the-snapshot)
- [Commit slices by behavior](#commit-slices-by-behavior)
- [Commit message policy](#commit-message-policy)
- [Agent commit attribution](#agent-commit-attribution)
- [Fixup commits and autosquash](#fixup-commits-and-autosquash)
- [Amend](#amend)

## Inspect the three states

**Definition.** HEAD is the last commit, the index is the proposed next
snapshot, and the worktree holds the current files. `git status --short`
shows two columns (index, worktree), `git diff --cached` shows index
versus HEAD, and `git diff` shows worktree versus index
([git-status][status], [git-diff][diff]).

**Use when.** Before and after every staging, commit, or history operation.

**Do not use when.** No exception. Changes staged by earlier work enter
the next commit unless you see and handle them.

**Example.**

```sh
git status --short --branch
git diff --cached --stat
git diff --stat
git log -5 --oneline
git worktree list
```

In `git status --short`, `M` in column 1 is staged, `M` in column 2 is
unstaged, and `??` is untracked.

**Cost removed.** Commits that carry unintended staged changes.

**Verify.**

1. `verify.sh` stages one file, edits another, adds an untracked file, and
   asserts the three porcelain lines for `README.md` (staged), `app.txt`
   (unstaged), and `untracked.txt`.

## Stage exact paths

**Definition.** `git add -- PATH...` stages the named paths; `git add -A`
and `git add .` stage everything, including files you did not mean to
commit.

**Use when.** Staging any change: name its paths.

**Do not use when.** No exception. Never use `-A` in a tree with unrelated
changes, build output, or secrets. Warn before staging a binary under
analysis (ELF, Mach-O, PE), a reference executable, or analysis output
such as `.ghidra-exports/`: they are usually licensed to the user alone,
and a pushed copy stays in history.

**Example.**

```sh
git add -- src/parser.py tests/test_parser.py
git diff --cached --stat   # only those two files
```

**Cost removed.** Secrets, generated files, and unrelated edits in
commits.

**Verify.**

1. `git diff --cached --name-only` lists exactly the intended paths.
1. `git diff --cached | rg -i 'secret|password|token|BEGIN .*PRIVATE KEY'`
   finds nothing.
1. `git diff --cached --numstat` shows no `-  -` (binary) rows you did
   not intend.

## Stage one hunk without a prompt

**Definition.** `git add -p` stages hunks interactively. The scripted,
reviewable equivalent writes the hunk to a patch and applies it to the
index alone with `git apply --cached` ([git-apply][apply]).

**Use when.** One file holds two independent changes for different
commits, and the agent cannot drive an interactive prompt.

**Do not use when.** The whole file belongs to one commit.

**Example.**

```sh
git diff -U0 app.txt > full.patch
awk '/^@@/{n++} n<2' full.patch > first.patch   # header + first hunk
git apply --cached --unidiff-zero first.patch
git diff --cached app.txt   # first hunk staged
git diff app.txt            # second hunk still unstaged
```

**Cost removed.** Unrelated changes mixed in one commit.

**Verify.**

1. `verify.sh` asserts line 1 is staged and line 5 is not.

## The commit --only trap

**Definition.** `git commit --only -- PATH` (also `git commit PATH`)
commits the path's current **worktree** content, ignoring what you staged
for it, and leaves other staged paths out ([git-commit][commit]).

**Use when.** You intend to commit a whole file as it is on disk.

**Do not use when.** The file is partially staged: the unstaged hunk goes
into the commit.

**Example.** Measured: after staging only the first hunk of `app.txt`,
`git commit --only -m msg -- app.txt` committed both hunks. Commit the
staged snapshot with plain `git commit -m msg` instead.

From `assets/examples/verify.sh`, run right after staging only the line 1
hunk (as in the previous card), with line 5 changed but unstaged:

```sh
# 3. commit --only records the path's worktree content, not staged hunks.
git commit -q --only -m 'only' -- app.txt
[ "$(git show HEAD:app.txt | sed -n 5p)" = 'line 5 CHANGED' ] ||
    fail commit-only 'expected the unstaged hunk to be committed'
pass 'commit --only -- path committed the unstaged hunk as well'
```

**Cost removed.** Unreviewed hunks entering a commit.

**Verify.**

1. `verify.sh` shows that the committed file contains the unstaged hunk.
1. After any commit, `git show --stat HEAD` and `git diff HEAD~1 --
   PATH` match what you reviewed.

## Snapshot identity with write-tree

**Definition.** `git write-tree` prints the tree ID of the current index.
If the commit recorded exactly that index, `git rev-parse HEAD^{tree}`
prints the same ID afterwards ([git-write-tree][write-tree]).

**Use when.** Exact snapshot identity matters: hooks may run, or the
reviewed index must be what gets committed.

**Do not use when.** No hook or tool can modify the index during commit.

**Example.**

```sh
expected=$(git write-tree)
git commit -m 'feat: add parser'
[ "$(git rev-parse 'HEAD^{tree}')" = "$expected" ] || echo 'tree changed'
```

**Cost removed.** Commits that differ from what was reviewed.

**Verify.**

1. `verify.sh` asserts equality for a plain commit.

## Existing hooks

**Definition.** Git runs hooks from `core.hooksPath` (default
`.git/hooks`); hook managers (lefthook, pre-commit, husky) install them.
Hooks are part of the repository's contract ([githooks][githooks]).

**Use when.** Before any commit or push, to find what will run.

**Do not use when.** You would bypass a failure with `--no-verify`,
install or replace hooks, or reset `core.hooksPath`, unless the user asked
for hook work.

**Example.**

```sh
git config --get core.hooksPath
ls "$(git rev-parse --git-path hooks)"
fd -H -d 1 'lefthook.yml|.pre-commit-config.yaml|.husky' .
```

**Cost removed.** Commits that CI rejects, and checks silently skipped.

**Verify.**

1. After a hook failure, `git log -1` shows no new commit and
   `git status` shows the index unchanged. Fix the cause and commit
   again.

## Hooks that change the snapshot

**Definition.** A `pre-commit` hook may edit and stage files (formatters),
so the committed tree can differ from the index you reviewed.

**Use when.** The repository has hooks (`core.hooksPath`, lefthook,
pre-commit, husky).

**Do not use when.** You would bypass a failing hook with `--no-verify`;
fix the cause instead.

**Example.** In `verify.sh`, a hook appends to `README.md` and stages it,
so `HEAD^{tree}` differs from the pre-commit `write-tree` value. Review
`git show HEAD` and rerun the checks on the committed tree. From
`assets/examples/verify.sh`:

```sh
# 5. A hook that edits the index changes the committed tree.
mkdir -p "$WORK/hooks"
cat >"$WORK/hooks/pre-commit" <<'EOF'
#!/bin/sh
echo 'added by hook' >>README.md
git add README.md
EOF
chmod +x "$WORK/hooks/pre-commit"
echo 'second' >>app.txt
git add app.txt
expected=$(git write-tree)
git -c core.hooksPath="$WORK/hooks" commit -q -m 'with hook'
[ "$(git rev-parse 'HEAD^{tree}')" != "$expected" ] ||
    fail hook-tree 'expected the hook to change the tree'
pass 'pre-commit hook changed the committed tree; write-tree detects it'
```

**Cost removed.** Unreviewed hook edits shipped silently.

**Verify.**

1. Compare `write-tree` before with `HEAD^{tree}` after every commit in a
   hooked repository; on mismatch, inspect `git show HEAD`.

## Commit slices by behavior

**Definition.** Each new commit holds one independently understandable,
revertible behavior with its tests and docs. Boundaries follow behavior,
not file names or diff size.

**Use when.** Committing a worktree with several changes, unless the
user asked for one commit.

**Do not use when.** Splitting would leave a commit that does not build or
pass its tests; keep dependent changes together.

**Example.**

```text
fix(parser): reject empty keys          src/parser.py, tests/test_parser.py
docs: document the keys option          docs/options.md
```

For each slice: stage it, review `git diff --cached`, run the checks that
cover it, and commit.

**Cost removed.** Reverting one change forces reverting another.

**Verify.**

1. For each commit, `git show --stat` lists only its slice, and its checks
   pass on that commit (`git stash -u`, test, `git stash pop`, or a linked
   worktree at that commit).

## Commit message policy

**Definition.** A repository's message rules come from its contributor
docs, commit linter config (for example `commitlint.config.*`), hooks,
and CI. Without a policy, default to
[Conventional Commits 1.0.0][cc]: `type(scope): summary`, `feat`/`fix`
and other types, and `!` or a `BREAKING CHANGE:` footer for incompatible
changes.

**Use when.** Writing or rewording any commit message.

**Do not use when.** You would imitate recent history against an explicit
policy, or install a linter just to write a message.

**Example.**

```sh
fd -H -d 2 'commitlint|\.czrc|lefthook|pre-commit-config' .
bunx commitlint --from HEAD~1 --to HEAD   # when commitlint is configured
```

```text
fix(bisect): abort instead of marking bad on missing command

A missing test command exited 127, which git bisect run treats as bad.
```

**Cost removed.** Pushes and CI runs rejected by message rules.

**Verify.**

1. The repository's message linter passes on the new commits.

## Agent commit attribution

**Definition.** When an agent writes a commit or pull request text, it
may mark its part with a trailer (`Co-Authored-By:`), an author or
committer name, or a line in the message. Whether to mark it, and how,
comes from the first of these sources that says anything:

1. Organization-managed harness settings (for Claude Code, managed
   settings), which override the rest.
1. Repository rules for agents: `AGENTS.md`, `CLAUDE.md`,
   `CONTRIBUTING.md`, an AI policy file, pull request templates, and
   the commit linter. A rule that forbids AI contributions stops the
   work; tell the user.
1. The user's own instructions, in the request or their personal agent
   instructions file. When they conflict with a repository rule, ask
   before committing.
1. The harness's attribution setting (table below), read from every
   settings file it merges.
1. Nothing set: the harness default.

| Harness | Setting | Where | Default |
| --- | --- | --- | --- |
| [Claude Code][cc-attribution] | `attribution.commit`, `attribution.pr` (strings), `attribution.sessionUrl` (Boolean), or `attribution: false`; deprecated `includeCoAuthoredBy` | `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed settings | `Co-Authored-By` trailer; pull request text |
| [Aider][aider-options] | `--attribute-co-authored-by`, `--attribute-author`, `--attribute-committer`, `--attribute-commit-message-author`, `--attribute-commit-message-committer` | flags, or `AIDER_ATTRIBUTE_*` environment variables | `Co-authored-by` trailer; no message prefix |
| [GitHub Copilot CLI][copilot-cli] | `includeCoAuthoredBy` (Boolean) | `~/.copilot/settings.json`, `.github/copilot/settings.json`, `.github/copilot/settings.local.json` (repository wins) | `true` |
| [Cursor agent and CLI][cursor-cli] | `attribution.attributeCommitsToAgent`, `attribution.attributePRsToAgent` (Booleans) | Cursor CLI configuration | `true` ("Made with Cursor") |

Codex CLI, Gemini CLI, and OpenCode list no attribution setting in their
configuration references (checked 2026-09-30); follow the repository and
the user. For another harness, find the setting in its documentation
before you state one. Keep the configured Git identity (`user.name`,
`user.email`); attribution never changes it.

**Use when.** An agent writes, amends, or rewords a commit or drafts a
pull request.

**Do not use when.** A person writes the commit; their message is theirs.

**Example.**

```sh
rg -n -i 'co-authored|attribution|ai[- ]generated|assisted' \
  AGENTS.md CLAUDE.md CONTRIBUTING.md .github 2>/dev/null
jq -c '{attribution, includeCoAuthoredBy}' ~/.claude/settings.json \
  .claude/settings.json .claude/settings.local.json 2>/dev/null
```

In Claude Code, `"attribution": false` hides all attribution (Claude
Code v2.1.281 or later; earlier versions skip the settings file that
holds it). Setting `commit` or `pr` makes Claude Code ignore
`includeCoAuthoredBy`.

**Cost removed.** Commits rejected by a project that requires or forbids
AI disclosure, and trailers the user turned off.

**Verify.**

1. `git log -1 --format=%B` ends with the attribution the first
   applicable source asks for, or none when it says none.
1. `git log -1 --format='%an <%ae>'` is the configured identity.

## Fixup commits and autosquash

**Definition.** `git commit --fixup=COMMIT` creates a commit titled
`fixup! <subject>`; `git rebase -i --autosquash BASE` moves it and folds it
into its target. `GIT_SEQUENCE_EDITOR=true` accepts the generated todo
list non-interactively ([git-rebase][rebase]).

**Use when.** Correcting an unpublished commit in a series and keeping the
series reviewable.

**Do not use when.** The target commit is on a shared branch and nobody
authorized rewriting it.

**Example.**

```sh
git commit --fixup "$TARGET"
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$TARGET~1"
```

**Cost removed.** Separate "fix typo" commits in history.

**Verify.**

1. `verify.sh` asserts the subjects after the rebase and that the target
   commit contains the fix.

## Amend

**Definition.** `git commit --amend` replaces HEAD with a new commit that
records the current index and either a new message or the same one
(`--no-edit`). The old commit stays reachable through the reflog.

**Use when.** The last commit is unpublished and the user asked to change
it.

**Do not use when.** The commit is pushed to a shared branch, or a hook
failed: the commit did not happen, so amending would modify the previous
one.

**Example.**

```sh
git add -- forgotten_test.py
git commit --amend --no-edit
```

**Cost removed.** An extra commit for a forgotten file.

**Verify.**

1. `git show --stat HEAD` includes the file; `git reflog -2` shows the
   amended commit.

[githooks]: https://git-scm.com/docs/githooks
[status]: https://git-scm.com/docs/git-status
[diff]: https://git-scm.com/docs/git-diff
[apply]: https://git-scm.com/docs/git-apply
[commit]: https://git-scm.com/docs/git-commit
[write-tree]: https://git-scm.com/docs/git-write-tree
[rebase]: https://git-scm.com/docs/git-rebase
[cc]: https://www.conventionalcommits.org/en/v1.0.0/
[cc-attribution]: https://code.claude.com/docs/en/settings#attribution-settings
[aider-options]: https://aider.chat/docs/config/options.html
[copilot-cli]: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference
[cursor-cli]: https://cursor.com/docs/cli/reference/configuration
