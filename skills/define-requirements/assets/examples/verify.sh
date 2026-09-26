#!/usr/bin/env sh
# Checks the worked specification, the vague draft, the acceptance tests,
# and that the tests fail when the implementation breaks a requirement.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CHECK="$ROOT/../../scripts/check_requirements.py"
PY=${PYTHON:-python3}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0

"$PY" "$CHECK" "$ROOT/export-cancellation-spec.md"
echo 'PASS worked spec has no defects'

status=0
out=$("$PY" "$CHECK" "$ROOT/vague-spec.md") || status=$?
[ "$status" -eq 1 ] || { echo 'FAIL vague spec passed' >&2; exit 1; }
echo "PASS vague draft rejected: $(echo "$out" | head -1)"

cp "$ROOT/export_cancel.py" "$ROOT/test_export_cancel.py" "$WORK/"
PYTHONDONTWRITEBYTECODE=1 "$PY" "$WORK/test_export_cancel.py" 2>&1 | tail -1
echo 'PASS acceptance tests'

# Mutation: publish even after cancellation (violates REQ-EXP-002).
sed 's/if self.state == "cancelled":/if False:/' "$ROOT/export_cancel.py" \
    >"$WORK/export_cancel.py"
if PYTHONDONTWRITEBYTECODE=1 "$PY" "$WORK/test_export_cancel.py" \
    >"$WORK/mutant.log" 2>&1; then
    echo 'FAIL acceptance tests missed the mutation' >&2
    exit 1
fi
grep -q 'test_ac_exp_001' "$WORK/mutant.log"
echo 'PASS AC-EXP-001 fails when a cancelled job still publishes'
echo 'VERIFY PASSED'
