#!/usr/bin/env sh
# Checks the plan and gate tools, and shows worktree isolation with git.
#
#   sh verify.sh
#
# The git part builds a throwaway repository, gives two "workers" their
# own worktrees and branches, and integrates them: disjoint ownership
# merges cleanly; shared ownership of one file conflicts.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
S="$ROOT/../../scripts"
PYTHON=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

"$PYTHON" "$S/test_checks.py" >"$WORK/t.log" 2>&1 || fail "$(tail -n 20 "$WORK/t.log")"
ok "checkers: $(grep -E '^Ran ' "$WORK/t.log")"

"$PYTHON" "$S/check_work_items.py" "$ROOT/work-items.json" >"$WORK/p.log" ||
    fail "plan: $(cat "$WORK/p.log")"
ok "plan: $(head -n 2 "$WORK/p.log" | tr '\n' ';')"
if "$PYTHON" "$S/check_work_items.py" "$ROOT/work-items.conflict.json" >"$WORK/c.log"; then
    fail "conflicting plan accepted"
fi
grep -q "both own 'src/common.py'" "$WORK/c.log" || fail "overlap not found"
grep -q "not the current phase" "$WORK/c.log" || fail "phase leak not found"
ok "conflicting plan: shared src/common.py and a release item rejected"

"$PYTHON" "$S/check_gate.py" "$ROOT/gate-implementation.json" >/dev/null ||
    fail "implementation gate should close"
if "$PYTHON" "$S/check_gate.py" "$ROOT/gate-verification.json" >"$WORK/g.log"; then
    fail "verification gate closed with unavailable evidence"
fi
grep -q 'C2: unavailable' "$WORK/g.log" || fail "unavailable not reported"
grep -q 'C3: not_run' "$WORK/g.log" || fail "not_run not reported"
ok "gates: implementation closes; verification stays open (unavailable, not_run)"

# Worktree isolation.
repo="$WORK/repo"
git init -q -b main "$repo"
git -C "$repo" config user.email verify@example.invalid
git -C "$repo" config user.name verify
mkdir -p "$repo/src"
printf 'shared = 1\n' >"$repo/src/common.py"
git -C "$repo" add . && git -C "$repo" commit -q -m base
work() { # name file content
    git -C "$repo" worktree add -q -b "$1" "$WORK/wt-$1" main
    mkdir -p "$(dirname "$WORK/wt-$1/$2")"
    printf '%s\n' "$3" >"$WORK/wt-$1/$2"
    git -C "$WORK/wt-$1" add . && git -C "$WORK/wt-$1" commit -q -m "$1"
}
work parser src/parser/__init__.py 'parse = 1'
work store src/store/__init__.py 'store = 1'
git -C "$repo" merge -q --no-edit parser store >/dev/null || fail "disjoint merge failed"
for f in src/parser/__init__.py src/store/__init__.py; do
    [ -f "$repo/$f" ] || fail "merged file missing: $f"
done
ok "disjoint ownership: two worktrees merge without conflict"
work left src/common.py 'shared = 2'
work right src/common.py 'shared = 3'
git -C "$repo" merge -q --no-edit left
if git -C "$repo" merge -q --no-edit right >"$WORK/m.log" 2>&1; then
    fail "shared file merged silently"
fi
git -C "$repo" diff --name-only --diff-filter=U | grep -q 'src/common.py' ||
    fail "conflict not on src/common.py"
git -C "$repo" merge --abort
ok "shared ownership: second merge conflicts on src/common.py (integrator must decide)"

echo "$PASS checks passed"
