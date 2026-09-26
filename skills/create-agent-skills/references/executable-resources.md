# Executable resources

Scripts and runnable examples turn instructions into checks an agent can
run. Per Anthropic, scripts solve problems instead of deferring them,
handle errors explicitly, avoid unexplained constants, and state whether
to execute or read them ([best practices][anthropic-bp],
[using scripts][using-scripts]).

## Contents

- Deterministic helper script
- Exit-code contract
- Disposable-copy verifier
- Equivalence oracle with a benefit assertion
- SKIP versus FAIL
- Plan-validate-execute

## Deterministic helper script

**Definition.** A standalone program in `scripts/` that does one
mechanical task (parse, compare, validate, generate), with documented
usage, explicit error messages, and its own tests.

**Use when.**

- The same logic would otherwise be regenerated for each task (comparing
  benchmark exports, parsing a changelog, checking links).
- Exact handling matters: units, row identity, exit codes, edge cases.

**Do not use when.**

- A maintained tool already does it; call that tool.
- The decision needs judgment (is this refactor safe?). A script can only
  report facts for the agent to judge.

**Example.** The checker bundled with this skill:

```python
def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    problems: list[str] = []
    for raw in argv:
        skill = Path(raw)
        if not skill.is_dir():
            print(f"error: {raw} is not a directory", file=sys.stderr)
            return 2
        problems.extend(check_skill(skill))
    for problem in problems:
        print(problem)
    return 1 if problems else 0
```

Runnable: `scripts/check_reference_structure.py`, tested by
`scripts/test_check_reference_structure.py`.

**Cost removed.** Inconsistent regenerated logic and the tokens spent
writing it; only the script's output enters context.

**Verify.**

1. `python3 scripts/test_<name>.py` passes with the standard library only.
1. `python3 scripts/<name>.py` with no arguments prints usage and exits 2.

## Exit-code contract

**Definition.** A documented mapping from outcome to exit status, for
example `0` success, `1` the checked condition failed, `2` invalid input
or usage. Callers and agents branch on the status instead of parsing
prose.

**Use when.** Any script or verifier an agent or CI runs.

**Do not use when.** Never exit 0 after a failure, and never swallow a
failing sub-command (`|| true`) to "keep going".

**Example.**

```text
Exit status: 0 within threshold, 1 regression, 2 invalid or
incomparable input. No files are modified.
```

(From `optimize-csharp-code/scripts/compare_benchmarks.py`.)

**Cost removed.** Failures reported as success.

**Verify.**

1. Tests assert each status: 0 for a passing input, 1 for a failing
   input, 2 for a malformed input.

## Disposable-copy verifier

**Definition.** A `verify.sh` that copies the example sources to a
`mktemp -d` directory, builds and runs them there, and removes the copy
on exit, so no build output lands in the skill directory.

**Use when.** A skill ships runnable examples in compiled languages or
with generated artifacts.

**Do not use when.** The example is a single interpreted file with no
outputs; run it directly.

**Example.**

```sh
#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark) ;;
    *) echo 'usage: verify.sh [verify|benchmark]' >&2; exit 2 ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
cp -R "$ROOT/constructs/." "$WORK/"
dotnet build "$WORK/Constructs.csproj" -c Release --nologo -v quiet
dotnet "$WORK/bin/Release/net10.0/Constructs.dll" "$MODE"
```

**Cost removed.** Stale `bin/`, `target/`, or `node_modules/` committed
into a published skill, and builds that depend on leftovers.

**Verify.**

1. `git status --short <skill-dir>` is identical before and after running
   every mode.
1. `shellcheck verify.sh` is clean.

## Equivalence oracle with a benefit assertion

**Definition.** For every before/after construct pair, a check that (a)
compares baseline and candidate outputs, including exceptions, on normal
and edge inputs, and (b) asserts the claimed benefit with a deterministic
measurement (allocated bytes, executed instructions, nesting depth, a
compiler diagnostic), preferred over wall time.

**Use when.** A card claims a transformation preserves behavior and
reduces a cost.

**Do not use when.** The benefit shows only in timing. Use the language's
benchmark harness and report the variance, and keep the oracle for
equivalence.

**Example.**

```csharp
Check.Equal("span-parsing", SpanParsing.BaselineSum(csv),
    SpanParsing.CandidateSum(csv));
Check.NoAllocation("span-parsing",
    () => SpanParsing.CandidateSum(csv));
```

**Cost removed.** Optimizations that change behavior, and unchecked
benefit claims.

**Verify.**

1. A deliberately broken candidate (wrong value, added allocation) makes
   the oracle fail with the construct's name.

## SKIP versus FAIL

**Definition.** A verifier prints `SKIP <check>: <tool> not found` and
continues when a toolchain is absent, and exits non-zero when a check
that ran failed.

**Use when.** Examples span toolchains a given machine may lack (Swift,
Kotlin, a GPU driver).

**Do not use when.** The missing tool is the skill's core requirement;
fail with a clear message.

**Example.**

```sh
have() { command -v "$1" >/dev/null 2>&1; }
if have kotlinc; then
    kotlinc -Werror template.kt -d out.jar
    echo 'PASS kotlin'
else
    echo 'SKIP kotlin: kotlinc not found'
fi
```

**Cost removed.** Verifiers that fail on every partial machine or
silently pass without checking.

**Verify.**

1. With one tool stripped from `PATH`, the output shows `SKIP` for it,
   and the exit status is 0 if everything else passed.

## Plan-validate-execute

**Definition.** For batch or destructive operations, the agent writes an
intermediate plan file (JSON, YAML), a script validates it against the
real state, and only then does a separate step execute it
([best practices][anthropic-bp]).

**Use when.** Bulk edits, migrations, remote writes, or anything hard to
undo.

**Do not use when.** The operation is a single reversible command.

**Example.**

```sh
python3 scripts/plan_renames.py src/ > renames.json
python3 scripts/validate_renames.py renames.json   # exit 1 lists conflicts
python3 scripts/apply_renames.py renames.json
```

**Cost removed.** Half-applied batch changes, and errors found only
after execution.

**Verify.**

1. The validator's tests reject a plan with a known conflict, with an
   error naming the offending entry.

[anthropic-bp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[using-scripts]: https://agentskills.io/skill-creation/using-scripts
