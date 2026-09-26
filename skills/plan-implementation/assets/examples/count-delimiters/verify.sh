#!/usr/bin/env sh
# Checks the worked plan and its vague draft, audits the worked plan's
# claims, then runs every Verify command of the worked plan against the
# demo project in a temp copy.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CHECK="$ROOT/../../../scripts/check_plan.py"
AUDIT="$ROOT/../../../scripts/audit_plan_claims.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0

"$PY" "$CHECK" "$ROOT/delimiter-plan.md"
echo 'PASS worked plan has no structural defects'

status=0
"$PY" "$CHECK" "$ROOT/vague-plan.md" >"$WORK/vague.log" || status=$?
cat "$WORK/vague.log"
[ "$status" -eq 1 ] || { echo 'FAIL vague plan passed' >&2; exit 1; }
grep -q 'cycle:' "$WORK/vague.log"
echo 'PASS vague plan rejected (including a dependency cycle)'

cp -R "$ROOT/demo/." "$WORK/"
"$PY" "$AUDIT" "$ROOT/delimiter-plan.md" "$WORK" >/dev/null
echo 'PASS every file and command the worked plan names exists'

cd "$WORK"
"$PY" "$CHECK" --commands "$ROOT/delimiter-plan.md" | sort -u |
    while IFS= read -r command; do
        sh -c "$command" >/dev/null 2>&1 ||
            { echo "FAIL plan command failed: $command" >&2; exit 1; }
        echo "PASS ran: $command"
    done
"$PY" bench.py
echo 'VERIFY PASSED'
