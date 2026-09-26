# Subagents

Running workers on a real host: spawning, briefing, isolation, review,
and the results workers return. The host facts come from the
[Claude Code subagents][cc] and [Codex subagents][cx] docs, fetched on
2026-09-25. The git isolation example runs in `assets/examples/verify.sh`.

## Contents

- Host capabilities
- Work-item brief
- Worker result contract
- Parallel waves from ownership
- Worktree isolation
- Independent review
- Coordination failure diagnosis

## Host capabilities

**Definition.** The operations the orchestrator needs:

- spawn an isolated context;
- scope its tools and paths;
- wait for a result;
- tell results apart;
- run workers in parallel;
- cancel a worker.

Map each one to the host's real feature. On Claude Code:

- subagents are Markdown files in `.claude/agents/` or
  `~/.claude/agents/`;
- their frontmatter sets `tools`, `disallowedTools`, `model`,
  `permissionMode`, `maxTurns`, `background`, and
  `isolation: worktree`.

On Codex:

- custom agents are TOML files in `.codex/agents/` or `~/.codex/agents/`,
  with `name`, `description`, and `developer_instructions`;
- subagents inherit the sandbox policy;
- `agents.max_concurrent_threads_per_session` caps parallel threads.

**Use when.** Planning the run, before you promise parallelism.

**Do not use when.** The host lacks a capability. State the limit and run
the work in sequence; do not build a wrapper.

**Example.** A read-only reviewer on Claude Code:

```markdown
---
name: defect-reviewer
description: Reviews a diff against frozen requirements; reports findings only.
tools: Read, Grep, Glob, Bash
permissionMode: plan
---
Review only the diff and requirement IDs you are given. Report each
defect with file:line, the violated requirement, and evidence.
```

**Cost removed.** Plans that assume parallel, isolated workers the host
does not provide.

**Verify.**

1. The plan names the host feature behind each capability and its limits,
   such as a concurrency cap.

## Work-item brief

**Definition.** A worker starts without the orchestrator's conversation,
so its brief holds everything it needs:

- the goal and the requirement IDs;
- the design baseline version and the base revision;
- the paths it owns;
- its dependencies;
- its constraints, including forbidden shortcuts;
- the local check command;
- the result format.

**Use when.** Spawning any worker.

**Do not use when.** You would paste the whole design document. Give only
the parts of the baseline the item touches.

**Example.** Fill in `assets/subagent-software-work-item.template.md`.
State this forbidden shortcut explicitly: "Do not stub a function to
make the build pass."

**Cost removed.** Workers redefining the goal, or doing the right work
in the wrong files.

**Verify.**

1. Every field of the template is filled in, or marked not applicable.

## Worker result contract

**Definition.** Every worker returns:

1. the work-item ID and role;
1. the files it examined or changed;
1. the outcome;
1. the commands it ran, with their results;
1. findings or blockers, with evidence;
1. whether it stayed inside its owned scope;
1. the commit or patch reference.

A narrative claim without evidence is not a result.

**Use when.** Accepting any worker output.

**Do not use when.** A result lacks command evidence. Send it back
instead of merging it.

**Example.** The orchestrator compares `git diff --name-only` against
the item's `owns` before accepting the result.

**Cost removed.** Merged work nobody tested, and scope violations found
late.

**Verify.**

1. For each accepted result, the report quotes its check command and
   outcome.

## Parallel waves from ownership

**Definition.** Two items can run together only when neither depends
on the other and their owned paths do not overlap. A directory
contains its files, so `src/` overlaps with `src/x.py`.
`check_work_items.py` computes the waves.

**Use when.** Deciding what to spawn together.

**Do not use when.** You would run more workers than the host cap or the
review capacity allows. A wave is an upper bound on parallelism, not a
target.

**Example.**

```text
$ python3 scripts/check_work_items.py assets/examples/work-items.conflict.json
error: release-notes: phase 'release' is not the current phase 'implementation'
error: parser and store can run in parallel but both own
  'src/common.py' / 'src/common.py'   (one line in the real output)
```

**Cost removed.** Workers overwriting each other's files, and work
from a later phase slipping into the current one.

**Verify.**

1. `check_work_items.py` exits 0 before the wave is spawned.

## Worktree isolation

**Definition.** Each worker writes in its own git worktree and branch
(`git worktree add -b ITEM PATH BASE`). Claude Code offers
`isolation: worktree`. The orchestrator integrates by merging, in the
planned order. Workers never run `reset --hard`, `clean -fdx`, shared
stashes, or force pushes.

**Use when.** Workers edit files in parallel.

**Do not use when.** Workers are read-only, like reviewers and explorers.

**Example.** From `verify.sh`, with two workers and disjoint paths:

```sh
git worktree add -q -b parser ../wt-parser main
git worktree add -q -b store ../wt-store main
git merge -q --no-edit parser store     # clean
```

When two workers both change `src/common.py`, the second merge conflicts
on that file, and `git merge --abort` restores the tree for the
integrator to decide.

**Cost removed.** Lost work from shared-checkout races.

**Verify.**

1. `verify.sh` shows the clean merge and the conflict on
   `src/common.py`.

## Independent review

**Definition.** A reviewer receives the diff, the frozen contracts, and
the test evidence, but not the implementer's private reasoning. It
reports findings; it does not edit. Each finding is then:

- accepted (fix it);
- rejected, with counter-evidence;
- an upstream defect (a baseline change);
- a duplicate;
- out of scope.

**Use when.** A unit is ready to integrate. Default to zero or one review
per unit; add a specialist review only for a distinct material risk, such
as concurrency or security.

**Do not use when.** The review would repeat checks the tests enforce.

**Example.** Spawn the `defect-reviewer` from the host card, with the
item's diff and requirement IDs.
`assets/software-defect-review.template.md` records the dispositions.

**Cost removed.** Defects hidden by the implementer's own framing.

**Verify.**

1. Every finding has a disposition, and every accepted fix has a rerun
   check.

## Coordination failure diagnosis

**Definition.** Each symptom points to a process defect upstream:

| Symptom | Process defect | Action |
| --- | --- | --- |
| Incompatible interfaces | Design underspecified or versions differ | Stop affected items; fix baseline |
| Workers stub failing code | Success condition rewards compiling | Tighten the item's check to behavior |
| Same defect in many items | Shared design rule wrong | Baseline change request |
| Overwritten changes | Ownership plan invalid | Rerun `check_work_items.py`; isolate worktrees |
| One huge log per worker | Failure queue not partitioned | Capture once; split by owner and cause |
| Tests changed to pass | Check weakened | Compare with the requirement; revert |

**Use when.** A wave produces conflicting or failing results.

**Do not use when.** The failure is an ordinary bug in one item. Fix it
in that item.

**Example.** Three items fail on the same date format: one upstream
design rule, so one change request, not three local fixes.

**Cost removed.** The same fix repeated across workers.

**Verify.**

1. The diagnosis names the changed upstream artifact and shows the
   affected items rerun.

[cc]: https://code.claude.com/docs/en/sub-agents
[cx]: https://developers.openai.com/codex/subagents
