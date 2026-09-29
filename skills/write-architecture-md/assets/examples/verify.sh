#!/usr/bin/env sh
# Copies the shortlinks example to a temporary directory, checks its
# ARCHITECTURE.md, runs every command it lists, proves the invariant check
# catches a violation, and proves the checker rejects the broken document.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CHECK="$ROOT/../../scripts/check_architecture.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
cp -R "$ROOT/shortlinks" "$WORK/shortlinks"
cd "$WORK/shortlinks"

"$PY" "$CHECK" ARCHITECTURE.md
echo 'PASS good document: 0 errors'

"$PY" "$CHECK" --commands ARCHITECTURE.md >"$WORK/commands.txt"
count=0
while IFS= read -r command; do
    sh -c "$command" >/dev/null 2>&1 ||
        { echo "FAIL listed command failed: $command" >&2; exit 1; }
    count=$((count + 1))
    echo "PASS ran: $command"
done <"$WORK/commands.txt"
[ "$count" -eq 3 ] || { echo "FAIL expected 3 commands, got $count" >&2; exit 1; }

# The invariant command must fail once the HTTP layer imports sqlite3.
invariant=$(sed -n 2p "$WORK/commands.txt")
printf 'import sqlite3\n' >>shortlinks/http.py
if sh -c "$invariant" >/dev/null 2>&1; then
    echo 'FAIL invariant check missed sqlite3 in http.py' >&2
    exit 1
fi
echo 'PASS invariant check catches sqlite3 imported by http.py'

cp "$ROOT/ARCHITECTURE.broken.txt" ARCHITECTURE.md
status=0
"$PY" "$CHECK" ARCHITECTURE.md >"$WORK/broken.log" || status=$?
cat "$WORK/broken.log"
[ "$status" -eq 1 ] || { echo 'FAIL broken document passed' >&2; exit 1; }
for expected in \
    "tree names 'shortlinks/handlers.py'" \
    "names \`shortlinks/handlers.py\`" \
    "template text left" \
    "section '5. External Integrations / APIs' is empty" \
    "diagram section has no fenced" \
    "top-level directory 'tests/' is not described" \
    "link to local file" \
    "file:line reference" \
    "self-contained"; do
    grep -qF "$expected" "$WORK/broken.log" ||
        { echo "FAIL checker did not report: $expected" >&2; exit 1; }
done
echo 'PASS broken document: every planted defect reported'

# The checker cannot see invented technology; a search for evidence can.
for claim in redis postgres jwt ecs; do
    if grep -rqi "$claim" shortlinks tests; then
        echo "FAIL $claim has evidence in the code" >&2
        exit 1
    fi
done
echo 'PASS Redis, PostgreSQL, JWT, and ECS have no evidence in the code'
echo 'VERIFY PASSED'
