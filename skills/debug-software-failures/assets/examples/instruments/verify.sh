#!/usr/bin/env sh
# Runs each diagnostic instrument against a program with a known fault and
# checks that its output locates the fault.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
have() { command -v "$1" >/dev/null 2>&1; }

status=0
"$PY" "$ROOT/py_deadlock.py" 2 >"$WORK/py.log" 2>&1 || status=$?
grep -o 'line [0-9]* in transfer_[a-z_]*' "$WORK/py.log"
for name in transfer_a_to_b transfer_b_to_a; do
    grep -q "in $name" "$WORK/py.log" ||
        { echo "FAIL faulthandler did not show $name" >&2; exit 1; }
done
echo "PASS faulthandler dump shows both threads at their second lock (exit $status)"

if have go; then
    status=0
    (cd "$WORK" && cp "$ROOT/deadlock.go" main.go &&
        go run main.go >go.log 2>&1) || status=$?
    grep -q 'all goroutines are asleep - deadlock!' "$WORK/go.log"
    grep -m1 'main.go:[0-9]*' -o "$WORK/go.log"
    echo "PASS Go runtime reports the deadlock and the blocked line (exit $status)"
else echo 'SKIP go: not installed'; fi

if have javac && have jcmd; then
    javac -d "$WORK" "$ROOT/Deadlock.java"
    java -cp "$WORK" Deadlock >"$WORK/java.out" 2>&1 &
    pid=$!
    tries=0
    until grep -q started "$WORK/java.out" 2>/dev/null; do
        tries=$((tries + 1)); [ "$tries" -gt 50 ] && break; sleep 0.1
    done
    sleep 1
    jcmd "$pid" Thread.print >"$WORK/threads.txt"
    kill "$pid"
    grep -q 'Found one Java-level deadlock' "$WORK/threads.txt"
    grep -m2 'Deadlock.java:[0-9]*' -o "$WORK/threads.txt"
    echo 'PASS jcmd Thread.print reports the Java-level deadlock'
else echo 'SKIP java: javac or jcmd not installed'; fi

pick_sdk() {
    printf 'int main(void){return 0;}\n' >"$WORK/t.c"
    cc "$WORK/t.c" -o "$WORK/t" 2>/dev/null && return 0
    for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.*.sdk; do
        if SDKROOT="$sdk" cc "$WORK/t.c" -o "$WORK/t" 2>/dev/null; then
            export SDKROOT="$sdk"
            return 0
        fi
    done
    return 1
}
if have cc && have lldb && pick_sdk; then
    cc -g -O0 "$ROOT/crash.c" -o "$WORK/crash"
    # -k runs only if the target crashes; without "-k quit" batch mode can
    # wait on the stopped process (observed with the swiftly lldb).
    lldb --batch -o run -k bt -k quit -- "$WORK/crash" >"$WORK/lldb.log" 2>&1 ||
        true
    grep -q 'name_length' "$WORK/lldb.log"
    want=$(grep -n 'config->name\[length\]' "$ROOT/crash.c" | cut -d: -f1)
    got=$(grep -m1 -o 'crash.c:[0-9]*' "$WORK/lldb.log" | cut -d: -f2)
    [ "$got" = "$want" ] || {
        echo "lldb stopped at crash.c:$got, expected $want" >&2
        exit 1
    }
    echo "PASS lldb backtrace names name_length and crash.c:$got"
else echo 'SKIP lldb: cc, lldb, or a linkable SDK missing'; fi
echo 'VERIFY PASSED'
