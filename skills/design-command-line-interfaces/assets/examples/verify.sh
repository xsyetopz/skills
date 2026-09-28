#!/usr/bin/env sh
# Runs check_cli.py against the baseline and the candidate, then checks the
# candidate's behavior: streams, exit codes, --json, `-` for stdin,
# non-interactive deletes, the renamed subcommand's alias, and precedence.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CHECK="$ROOT/../../scripts/check_cli.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
# A regression that ignores --store must not write to the real home.
export HOME="$WORK/home" XDG_DATA_HOME="$WORK/data"
TODO="$PY $ROOT/todo.py"
STORE="$WORK/tasks.json"

fail() { echo "FAIL $*" >&2; exit 1; }

"$PY" "$CHECK" --timeout 3 --sub add --sub list --sub remove -- "$PY" "$ROOT/todo.py" \
    || fail 'candidate has check_cli.py findings'
echo 'PASS candidate: check_cli.py clean'

status=0
"$PY" "$CHECK" --timeout 3 --json -- "$PY" "$ROOT/todo_bad.py" >"$WORK/bad.json" || status=$?
[ "$status" -eq 1 ] || fail "baseline exited $status, expected 1"
for probe in unknown-flag stack-trace ansi-when-piped; do
    grep -q "\"probe\": \"$probe\"" "$WORK/bad.json" || fail "baseline missed $probe"
done
echo 'PASS baseline: rejected for unknown-flag, stack-trace, ansi-when-piped'

# Data on stdout, messages on stderr, no color in a pipe.
$TODO --store "$STORE" add "write notes" >"$WORK/out" 2>"$WORK/err"
[ ! -s "$WORK/out" ] || fail 'add wrote to stdout'
grep -q 'Added 1 task' "$WORK/err" || fail 'add did not report the change'
printf 'one\ntwo\n' | $TODO --store "$STORE" add - 2>/dev/null
[ "$($TODO --store "$STORE" list)" = "$(printf '1\twrite notes\n2\tone\n3\ttwo')" ] \
    || fail 'plain list output'
echo 'PASS streams, - reads stdin, plain one-record-per-line output'
$TODO --store "$WORK/dash.json" add -- -weird-title 2>/dev/null
[ "$($TODO --store "$WORK/dash.json" list | cut -f2)" = '-weird-title' ] || fail '-- did not end options'
echo 'PASS -- ends options'

$TODO --store "$STORE" list --json | "$PY" -c \
    'import json,sys; assert [t["title"] for t in json.load(sys.stdin)] == ["write notes","one","two"]'
echo 'PASS --json parses'

# Non-interactive delete: refuse without --force, exit 2, name the flag.
status=0
$TODO --store "$STORE" remove 2 </dev/null 2>"$WORK/err" || status=$?
[ "$status" -eq 2 ] || fail "remove without --force exited $status"
grep -q -- '--force' "$WORK/err" || fail 'refusal does not name --force'
$TODO --store "$STORE" remove 2 --force 2>/dev/null
echo 'PASS delete refuses without --force off a terminal, then --force deletes'

# Renamed subcommand: old name still works and warns on stderr.
$TODO --store "$STORE" rm 3 --force >"$WORK/out" 2>"$WORK/err"
grep -q 'deprecated.*todo remove' "$WORK/err" || fail 'alias did not warn'
[ ! -s "$WORK/out" ] || fail 'alias warning went to stdout'
$TODO --help | grep -q ' rm ' && fail 'deprecated alias listed in help'
echo 'PASS old name rm works, warns on stderr, hidden from help'

# Global flags work on either side of the subcommand.
$TODO list --store "$WORK/order.json" --quiet >/dev/null
$TODO --store "$WORK/order.json" --quiet add before 2>/dev/null
$TODO add after --store "$WORK/order.json" 2>/dev/null
[ "$($TODO list --store "$WORK/order.json" | cut -f2 | tr '\n' ' ')" = 'before after ' ] \
    || fail 'global flag position changed its meaning'
echo 'PASS --store works before and after the subcommand'

# Precedence: flag beats environment.
TODO_STORE="$WORK/env.json" $TODO --store "$STORE" add flagged 2>/dev/null
[ ! -e "$WORK/env.json" ] || fail 'environment beat the flag'
TODO_STORE="$WORK/env.json" $TODO add from-env 2>/dev/null
[ -e "$WORK/env.json" ] || fail 'environment ignored'
echo 'PASS --store beats TODO_STORE'

status=0
$TODO --store "$STORE" remove 99 --force 2>"$WORK/err" || status=$?
[ "$status" -eq 1 ] || fail "missing id exited $status"
grep -q 'todo list' "$WORK/err" || fail 'error does not say what to run next'
echo 'PASS runtime error exits 1 and suggests the next command'
# Unexpected error: short message, traceback in a log file, no trace on screen.
echo '{"not": "a list"}' >"$WORK/odd.json"
status=0
TMPDIR="$WORK" $TODO --store "$WORK/odd.json" list 2>"$WORK/err" || status=$?
[ "$status" -eq 1 ] || fail "internal error exited $status"
grep -q 'Traceback' "$WORK/err" && fail 'traceback printed to the terminal'
log=$(sed -n 's/.*details in \([^;]*\.log\)$/\1/p' "$WORK/err")
grep -q 'Traceback' "$log" || fail 'crash log has no traceback'
echo 'PASS internal error: two-line summary, traceback in the crash log'
echo 'VERIFY PASSED'
