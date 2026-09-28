#!/usr/bin/env sh
# Builds disposable Git histories with a known culprit and checks that each
# bisect technique in the skill finds it. Never touches the caller's repos:
# every repository lives under a mktemp directory with isolated Git config.
#
#   sh verify.sh        all scenarios
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
ORACLE="$ROOT/../../../scripts/bisect_oracle.py"
ORACLE=$(CDPATH='' cd -- "$(dirname -- "$ORACLE")" && pwd)/bisect_oracle.py
command -v git >/dev/null 2>&1 || {
    echo 'SKIP: git not found'
    exit 0
}
PY=${PYTHON:-python3}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM

# Isolate from the user's Git configuration, hooks, and signing.
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL="$WORK/gitconfig"
export GIT_AUTHOR_NAME=fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=fixture GIT_COMMITTER_EMAIL=fixture@example.invalid
git config --global init.defaultBranch main
git config --global commit.gpgSign false
git config --global advice.detachedHead false
PASSED=0

pass() {
    PASSED=$((PASSED + 1))
    echo "PASS $1"
}
fail() {
    echo "FAIL $1: $2" >&2
    exit 1
}

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

commit() {
    git add -A
    git commit -q -m "$1"
}

subject_of() {
    git -C "$1" log -1 --format=%s "$2"
}

# linear: 40 commits; commit 23 introduces the defect; commits 10-12 do not
# build (BROKEN_BUILD present); commit 31 is a later unrelated change.
make_linear() {
    repo=$1
    git init -q "$repo"
    (
        cd "$repo"
        printf 'def add(a, b):\n    return a + b\n' >calc.py
        : >notes.txt
        commit 'commit 1: initial'
        n=2
        while [ "$n" -le 40 ]; do
            # The culprit touches only calc.py so it reverts cleanly.
            [ "$n" -eq 23 ] || echo "change $n" >>notes.txt
            case $n in
                10) : >BROKEN_BUILD ;;
                13) rm BROKEN_BUILD ;;
                23) printf 'def add(a, b):\n    return a - b\n' >calc.py ;;
            esac
            if [ "$n" -eq 23 ]; then
                commit "commit $n: introduce regression"
            else
                commit "commit $n: routine change"
            fi
            n=$((n + 1))
        done
        git tag good-endpoint HEAD~39
        git tag bad-endpoint HEAD
    )
}

run_oracle() {
    "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- "$PY" "$WORK/check.py"
}

# 1. Endpoints: the same oracle must classify both ends before a search.
make_linear "$WORK/linear"
cd "$WORK/linear"
git checkout -q good-endpoint
run_oracle || fail endpoints 'good endpoint is not good'
git checkout -q bad-endpoint
status=0
run_oracle || status=$?
[ "$status" -eq 1 ] || fail endpoints "bad endpoint returned $status"
pass 'endpoints classified by the same oracle'

# 2. bisect run finds the culprit, skipping unbuildable commits.
git bisect start bad-endpoint good-endpoint >/dev/null
git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- \
    "$PY" "$WORK/check.py" >"$WORK/run.log" 2>&1
culprit=$(git rev-parse refs/bisect/bad)
[ "$(subject_of . "$culprit")" = 'commit 23: introduce regression' ] ||
    fail bisect-run "found $(subject_of . "$culprit")"
steps=$(grep -c '^Bisecting' "$WORK/run.log" || true)
git bisect log >"$WORK/linear.bisect.log"
git bisect reset >/dev/null
pass "bisect run found commit 23 in $steps steps over 39 candidates"

# 3. Culprit verification: parent good, culprit bad, revert on bad fixes it.
git checkout -q "$culprit^"
run_oracle || fail verify-parent 'parent of culprit is bad'
git checkout -q "$culprit"
status=0
run_oracle || status=$?
[ "$status" -eq 1 ] || fail verify-culprit "culprit returned $status"
git checkout -q -b revert-check bad-endpoint
git revert --no-edit "$culprit" >/dev/null
run_oracle || fail verify-revert 'reverting the culprit did not fix HEAD'
git checkout -q main
pass 'culprit verified: parent good, culprit bad, revert fixes bad'

# 4. Skip ambiguity: if the defect lands inside an untestable range, bisect
# can only report a set of candidates.
# Clean case: base is good; the defect lands in an unbuildable commit whose
# only neighbor is the build fix, so no testable commit separates them.
git init -q "$WORK/ambiguous"
cd "$WORK/ambiguous"
printf 'def add(a, b):\n    return a + b\n' >calc.py
commit 'base: good'
git tag base
printf 'def add(a, b):\n    return a - b\n' >calc.py
: >BROKEN_BUILD
commit 'defect introduced while build broken'
rm BROKEN_BUILD
commit 'build fixed'
git bisect start HEAD base >/dev/null
status=0
git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- \
    "$PY" "$WORK/check.py" >"$WORK/amb.log" 2>&1 || status=$?
grep -q "only 'skip'ped commits left" "$WORK/amb.log" ||
    fail skip-ambiguity 'bisect did not report skipped candidates'
git bisect reset >/dev/null
pass "skipped neighbors reported as ambiguous (bisect exit $status)"

# 5. Oracle safety: a missing command aborts instead of marking bad.
cd "$WORK/linear"
git bisect start bad-endpoint good-endpoint >/dev/null
status=0
git bisect run "$PY" "$ORACLE" -- "$WORK/does-not-exist" \
    >"$WORK/abort.log" 2>&1 || status=$?
[ "$status" -ne 0 ] || fail oracle-abort 'bisect run did not abort'
if git rev-parse -q --verify refs/bisect/bad >/dev/null &&
    [ "$(git rev-parse refs/bisect/bad)" != "$(git rev-parse bad-endpoint)" ]; then
    fail oracle-abort 'a revision was marked bad by an infrastructure error'
fi
git bisect reset >/dev/null
pass 'missing test command aborts bisect instead of marking bad'

# 6. Custom terms: find the commit that fixed a defect.
git init -q "$WORK/fixed"
cd "$WORK/fixed"
printf 'def add(a, b):\n    return a - b\n' >calc.py
commit 'broken since the start'
git tag broken
i=1
while [ "$i" -le 12 ]; do
    echo "$i" >>notes.txt
    if [ "$i" -eq 7 ]; then
        printf 'def add(a, b):\n    return a + b\n' >calc.py
        commit 'fix add'
    else
        commit "routine $i"
    fi
    i=$((i + 1))
done
git bisect start --term-old broken --term-new fixed HEAD broken >/dev/null
# With terms broken/fixed, exit 0 means "old" (broken): invert the oracle.
cat >"$WORK/is_broken.sh" <<EOF
#!/bin/sh
if "$PY" "$WORK/check.py"; then exit 1; else exit 0; fi
EOF
chmod +x "$WORK/is_broken.sh"
git bisect run "$WORK/is_broken.sh" >/dev/null 2>&1
[ "$(subject_of . refs/bisect/fixed)" = 'fix add' ] ||
    fail terms "found $(subject_of . refs/bisect/fixed)"
git bisect reset >/dev/null
pass 'custom terms (--term-old broken --term-new fixed) found the fix'

# 7. First parent: a defect introduced inside a merged branch is attributed
# to the merge commit.
git init -q "$WORK/merge"
cd "$WORK/merge"
printf 'def add(a, b):\n    return a + b\n' >calc.py
commit 'main: base'
git tag base
git checkout -q -b feature
echo feature >feature.txt
commit 'feature: step 1'
printf 'def add(a, b):\n    return a - b\n' >calc.py
commit 'feature: step 2 breaks add'
echo more >>feature.txt
commit 'feature: step 3'
git checkout -q main
echo main >main.txt
commit 'main: unrelated'
git merge -q --no-ff -m 'merge feature' feature
git bisect start --first-parent HEAD base >/dev/null
git bisect run "$PY" "$ORACLE" -- "$PY" "$WORK/check.py" >/dev/null 2>&1
[ "$(subject_of . refs/bisect/bad)" = 'merge feature' ] ||
    fail first-parent "found $(subject_of . refs/bisect/bad)"
git bisect reset >/dev/null
git bisect start HEAD base >/dev/null
git bisect run "$PY" "$ORACLE" -- "$PY" "$WORK/check.py" >/dev/null 2>&1
[ "$(subject_of . refs/bisect/bad)" = 'feature: step 2 breaks add' ] ||
    fail full-history "found $(subject_of . refs/bisect/bad)"
git bisect reset >/dev/null
pass 'first-parent finds the merge; full history finds the branch commit'

# 8. Path-limited search only visits commits touching the path.
cd "$WORK/linear"
git bisect start bad-endpoint good-endpoint -- calc.py >/dev/null
git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- \
    "$PY" "$WORK/check.py" >"$WORK/path.log" 2>&1
[ "$(subject_of . refs/bisect/bad)" = 'commit 23: introduce regression' ] ||
    fail pathspec 'wrong culprit'
path_steps=$(grep -c '^Bisecting' "$WORK/path.log" || true)
git bisect reset >/dev/null
pass "pathspec search found commit 23 in $path_steps steps"

# 9. Log and replay: correct a wrong manual mark.
git bisect start bad-endpoint good-endpoint >/dev/null
git bisect bad >/dev/null 2>&1 # a deliberate mistake at the first midpoint
git bisect log >"$WORK/mistake.log"
git bisect reset >/dev/null
# The log records the mark as `git bisect bad <hash>` after the `start`
# line; drop that line (and its `# bad:` comment) and keep the rest.
awk '/^git bisect start/{started=1} started && /^(git bisect bad |# bad:)/{next}
    {print}' "$WORK/mistake.log" >"$WORK/fixed.log"
grep -q '^git bisect bad ' "$WORK/fixed.log" && fail replay 'mark not removed'
git bisect replay "$WORK/fixed.log" >/dev/null
git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- \
    "$PY" "$WORK/check.py" >/dev/null 2>&1
[ "$(subject_of . refs/bisect/bad)" = 'commit 23: introduce regression' ] ||
    fail replay 'replayed session found the wrong commit'
git bisect reset >/dev/null
pass 'bisect log edited and replayed to remove a wrong mark'

# 10. Worktree isolation: the main checkout is untouched during the search.
before=$(git rev-parse HEAD)
echo 'uncommitted work' >"$WORK/linear/scratch.txt"
git worktree add -q --detach "$WORK/wt" bad-endpoint
git -C "$WORK/wt" bisect start bad-endpoint good-endpoint >/dev/null
(cd "$WORK/wt" && git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 \
    -- "$PY" "$WORK/check.py" >/dev/null 2>&1)
found=$(git -C "$WORK/wt" rev-parse refs/bisect/bad)
git -C "$WORK/wt" bisect reset >/dev/null
git worktree remove "$WORK/wt"
[ "$(git rev-parse HEAD)" = "$before" ] || fail worktree 'main HEAD moved'
[ -f scratch.txt ] || fail worktree 'uncommitted file lost'
[ "$(subject_of . "$found")" = 'commit 23: introduce regression' ] ||
    fail worktree 'wrong culprit'
pass 'bisect in a worktree left the main checkout and its files alone'

# 11. Flaky oracle: a spurious failure misleads a single-run search; a
# majority-of-three wrapper does not.
cat >"$WORK/flaky.sh" <<EOF
#!/bin/sh
# Fails spuriously on exactly the 1st invocation (the first midpoint, which
# is a good commit), like an intermittent test.
count=\$(cat "$WORK/flaky.count" 2>/dev/null || echo 0)
count=\$((count + 1))
echo "\$count" >"$WORK/flaky.count"
[ "\$count" -eq 1 ] && exit 1
exec "$PY" "$WORK/check.py"
EOF
cat >"$WORK/majority.sh" <<EOF
#!/bin/sh
# Run the test three times; report bad only if at least two runs fail.
fails=0
for _ in 1 2 3; do "$WORK/flaky.sh" || fails=\$((fails + 1)); done
[ "\$fails" -ge 2 ] && exit 1
exit 0
EOF
chmod +x "$WORK/flaky.sh" "$WORK/majority.sh"
rm -f "$WORK/flaky.count"
git bisect start bad-endpoint good-endpoint >/dev/null
git bisect run "$WORK/flaky.sh" >/dev/null 2>&1 || true
naive=$(subject_of . refs/bisect/bad)
git bisect reset >/dev/null
rm -f "$WORK/flaky.count"
git bisect start bad-endpoint good-endpoint >/dev/null
git bisect run "$WORK/majority.sh" >/dev/null 2>&1
majority=$(subject_of . refs/bisect/bad)
git bisect reset >/dev/null
[ "$majority" = 'commit 23: introduce regression' ] ||
    fail flaky "majority wrapper found $majority"
[ "$naive" != "$majority" ] ||
    fail flaky 'expected the single-run search to be misled'
pass "flaky test: single run blamed '$naive'; majority of 3 found commit 23"

# 12. Pickaxe finds when a text appeared without running anything.
[ "$(git log -S 'a - b' --format=%s -- calc.py)" = \
    'commit 23: introduce regression' ] || fail pickaxe 'git log -S missed'
pass 'git log -S finds the commit that introduced the text'

echo "VERIFY PASSED: $PASSED checks"
