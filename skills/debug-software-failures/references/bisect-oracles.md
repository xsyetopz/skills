# Bisect oracles and culprit verification

The oracle is the command that classifies one revision as good, bad
(target defect), or untestable. Its exit codes drive `git bisect run`, so
every non-target failure must become "skip" or "abort", never "bad".
[`bisect_oracle.py`](../scripts/bisect_oracle.py) implements the mapping;
the scenarios are in
[`assets/examples/bisect/verify.sh`](../assets/examples/bisect/verify.sh).

## Contents

- Exit-code mapping oracle
- Oracle outside the checkout
- Majority vote for flaky tests
- Threshold oracle for performance regressions
- Historical build environment
- Culprit verification: parent, culprit, revert
- Merge culprits

## Exit-code mapping oracle

**Definition.** A wrapper that runs the real test without a shell and maps
its status: 0 → 0 (good), listed defect statuses → 1 (bad), listed
untestable statuses → 125 (skip), anything else (missing command, signal,
timeout, unexpected status) → 128, which aborts the search
([bisect run exit codes][git-bisect]).

**Use when.** The test command can fail for reasons other than the target
defect. It almost always can: missing tools, compile errors, network.

**Do not use when.** The command is purpose-built and returns only 0 or 1
for the target symptom; call it directly.

**Example.**

```sh
python3 scripts/bisect_oracle.py --bad-exit 1 --skip-exit 3 \
  --timeout 300 -- python3 /abs/path/check.py
```

Exit 0 good, 1 known regression, 125 declared untestable, 128 abort.

**Cost removed.** False "bad" marks. POSIX shells return 127 for "command
not found" and 126 for "not executable", and `git bisect run` treats both
as bad ([git-bisect][git-bisect]).

**Verify.**

1. `python3 scripts/test_bisect_oracle.py` and
   `python3 scripts/test_bisect_integration.py` pass.
1. `verify.sh` runs a search with a missing test command and asserts it
   aborts without marking a revision bad.

## Oracle outside the checkout

**Definition.** Keep the test script at an absolute path outside the
bisected repository, so every checked-out revision runs the same test.

**Use when.** Any `git bisect run`.

**Do not use when.** The test must be the project's own test file at each
revision. The question then changes with the test; say so in the report.

**Example.** `verify.sh` writes `check.py` to its temporary directory and
passes `"$WORK/check.py"` to every search. From
`assets/examples/bisect/verify.sh`:

```sh
# The test oracle lives outside the history: exit 0 good, 1 bad (target
# defect), 3 cannot build (untestable).
cat >"$WORK/check.py" <<'EOF'
import pathlib
import sys

if pathlib.Path("BROKEN_BUILD").exists():
    sys.exit(3)
namespace = {}
exec(pathlib.Path("calc.py").read_text(), namespace)
sys.exit(0 if namespace["add"](2, 3) == 5 else 1)
EOF
```

The same file's `run_oracle` helper calls it by that path, absolute
because `WORK` comes from `mktemp -d`:

```sh
run_oracle() {
    "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- "$PY" "$WORK/check.py"
}
```

**Cost removed.** A test that changes or disappears as bisect checks out
older revisions.

**Verify.**

1. The path passed to `bisect run` is absolute and outside the repository
   (`git -C "$(dirname PATH)" rev-parse` fails or names another repo).

## Majority vote for flaky tests

**Definition.** Run the test K times per revision and mark it bad only if
at least M runs fail (for example, 2 of 3).

**Use when.** The test fails intermittently on good revisions. One
spurious failure sends binary search into the wrong half.

**Do not use when.** The flakiness rate is unknown. Measure it on the good
endpoint first (for example, 20 runs; see
[failure rate][rate]),
then choose K so a good revision rarely reaches M failures.

**Example.**

```sh
#!/bin/sh
fails=0
for _ in 1 2 3; do /abs/path/test.sh || fails=$((fails + 1)); done
[ "$fails" -ge 2 ] && exit 1
exit 0
```

**Cost removed.** Wrong culprits from noise. Measured: one spurious
failure on the first midpoint made a single-run search blame `commit 10:
routine change`; the majority-of-3 wrapper found commit 23.

**Verify.**

1. `verify.sh` runs both searches over the same history and asserts
   they differ, with the majority search correct.

## Threshold oracle for performance regressions

**Definition.** An oracle that measures a metric (time, allocations,
binary size) and exits 1 when it crosses a threshold placed between the
good and bad endpoints' measured distributions.

**Use when.** The regression is a measurable slowdown or growth with a
clear gap between endpoints.

**Do not use when.** The endpoints' distributions overlap. Improve the
measurement first: more runs, a quieter machine, or an operation count
instead of time.

**Example.**

```sh
#!/bin/sh
# Median of 10 runs in ms; 150 ms sits between good (~100) and bad (~200).
hyperfine -N --runs 10 --export-json /tmp/h.json './build/app --bench' \
  >/dev/null || exit 125
median=$(python3 -c 'import json; r=json.load(open("/tmp/h.json"))
print(int(r["results"][0]["median"] * 1000))')
[ "$median" -gt 150 ] && exit 1
exit 0
```

Start the search with `--term-old fast --term-new slow` so the report
reads naturally.

**Cost removed.** Commits misclassified by timing noise.

**Verify.**

1. Before the search, run the oracle 5 times on each endpoint: every good
   run exits 0 and every bad run exits 1.

## Historical build environment

**Definition.** Old revisions may need the toolchain, submodules, and
generated files of their time; today's environment can fail to build them
for unrelated reasons.

**Use when.** Old revisions fail to build, or fail differently from how
the good endpoint behaved originally.

**Do not use when.** You would map every such failure to "bad".

**Example.**

```sh
git submodule update --init --recursive   # per revision, in the oracle
# pinned toolchain from the revision, if the project has one:
[ -f rust-toolchain.toml ] && rustup show active-toolchain
```

Map "cannot build with this environment" to the skip status and report
how many commits were skipped.

**Cost removed.** Environment drift reported as a regression.

**Verify.**

1. `git bisect log` lists skipped commits; if they cluster at the
   transition, the result is ambiguous (see
   [bisect](bisect.md#ambiguity-when-skipped-commits-remain)).

## Culprit verification: parent, culprit, revert

**Definition.** Confirm the result three ways: the culprit's parent
passes the oracle, the culprit fails it, and reverting the culprit on top
of the bad endpoint makes the oracle pass.

**Use when.** Before reporting any culprit.

**Do not use when.** No exception. The revert check catches a culprit that
only exposed an older problem.

**Example.**

```sh
git checkout -q "$CULPRIT^" && /abs/path/oracle.sh   # expect 0
git checkout -q "$CULPRIT" && /abs/path/oracle.sh    # expect 1
git checkout -q -b verify-revert "$BAD"
git revert --no-edit "$CULPRIT" && /abs/path/oracle.sh   # expect 0
```

If the revert conflicts, report it, then apply the culprit's diff in
reverse to the bad endpoint by hand and test that; do not force it.

**Cost removed.** Blaming a commit that only correlates with the symptom.

**Verify.**

1. `verify.sh` runs all three checks on the found culprit.

## Merge culprits

**Definition.** When the first bad commit is a merge, the defect may come
from combining both sides rather than from either side alone.

**Use when.** `refs/bisect/bad` is a merge commit.

**Do not use when.** The search used `--first-parent` on purpose to find
the merge; that answer is complete.

**Example.**

```sh
git log -1 --format='%P' "$CULPRIT"   # two parents: P1 P2
git checkout -q P1 && /abs/path/oracle.sh
git checkout -q P2 && /abs/path/oracle.sh
```

If both parents pass, the merge itself introduced the defect (a semantic
conflict); report it that way.

**Cost removed.** Blaming the wrong branch.

**Verify.**

1. Report each parent's oracle status with the culprit.

[git-bisect]: https://git-scm.com/docs/git-bisect
[rate]: nondeterminism-and-packaging.md#failure-rate-over-repeated-runs
