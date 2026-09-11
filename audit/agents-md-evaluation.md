# Repository instruction maintenance evaluation

Evaluated 2026-09-12. Integrated `agents-md-creator` as the action-oriented
`maintain-agents-md`; it remains explicit-only. Consolidated five small
references into one without introducing a schema, template generator, or
required heading set.

## Source review and correction

Rechecked [AGENTS.md](https://agents.md/) and the official [Codex discovery
guide][codex]. The latter documents per-directory override precedence, the
launch-directory chain, configured fallback names, and a combined 32 KiB default
budget. These are Codex-specific behaviors, not guarantees for all consumers. No
personal Codex configuration was read or changed.

The inherited example incorrectly claimed that `bun test` invokes a manifest's
test script. A real Bun 1.4.2 fixture demonstrated the difference: `bun test`
ran a discovered test file, while `bun run test` executed a separately defined
script with a distinct output marker. The example now uses the latter for
manifest scripts and explains why the distinction matters. The [official Bun
runtime guide][bun] confirms builtin command precedence.

## Independent forward evaluation

A fresh-context evaluator received the skill and an isolated repository fixture
with conflicting root test instructions, CI commands, payment-specific
overrides, a stale shadowed standard file, and unrelated search instructions.
The task specified a payments launch directory and fixture project root; it
supplied no expected edits.

The output corrected the root command, retained no-publication and no-database
constraints, stated working directories and additive checks, and left unrelated
files unchanged. It correctly selected the root and payments override as the
project chain, identified the shadowed standard file, and excluded the sibling
search scope. Its chain is not proof of the global instruction layer, which was
outside the fixture.

Actual root and payments package scripts passed. The shadowed `npm test`
instruction failed because that script does not exist. The evaluator reported
this stale fallback rather than silently treating it as active or modifying
unrelated configuration. Future removal of the override requires reconciling
that file; this is a documented limitation, not a repaired fallback claim.

The scripts deliberately emit distinct markers to test command dispatch. Their
success is not application-test coverage. The real Bun test-runner probe is a
separate check. No hosted CI job or actual Codex loader session was executed.

## Validation

Both skill validators and strict Markdown pass. Local links resolve and metadata
requires manual invocation with the correct default-prompt name. Inspection of
the isolated diff confirms only the two intended instruction files changed;
application files, workflow, and sibling instructions are unchanged.

Raw report: `/tmp/agents-md-forward-result.md`. Evaluated copy:
`/tmp/agents-scope-copy.5A0B63`. The fixture and command-dispatch probe remain
in `/tmp`, outside the skill package. No executable assets were justified.

[codex]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[bun]: https://bun.sh/docs/runtime#run-a-package-json-script
