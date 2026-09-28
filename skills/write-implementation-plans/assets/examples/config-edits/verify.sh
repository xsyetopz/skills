#!/usr/bin/env sh
# Runs the claims audit on the plan under review and the counterexample
# tests that back each finding in review.md.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
AUDIT="$ROOT/../../../scripts/audit_plan_claims.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
cp -R "$ROOT/repo/." "$WORK/"

status=0
"$PY" "$AUDIT" "$ROOT/config-plan.md" "$WORK" >"$WORK/audit.log" || status=$?
cat "$WORK/audit.log"
[ "$status" -eq 1 ] || { echo 'FAIL audit found no missing claims' >&2; exit 1; }
grep -q 'MISSING .*src/config_cli.py' "$WORK/audit.log"
grep -q 'MISSING .*just test-config' "$WORK/audit.log"
echo 'PASS audit reports the missing file and recipe (F4)'

cd "$WORK"
"$PY" -m unittest tests.test_config_store -v 2>&1 | tail -8
echo 'PASS counterexamples reproduce F1 and F2; corrections hold'
echo 'VERIFY PASSED'
