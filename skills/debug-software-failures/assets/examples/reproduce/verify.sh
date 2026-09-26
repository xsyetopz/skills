#!/usr/bin/env sh
# Reproduces each example failure with its oracle, reduces the CSV input
# with ddmin, and shows forced versus timing-dependent race reproduction.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
DDMIN="$ROOT/../../../scripts/ddmin.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0

"$PY" "$ROOT/python-delimiter-repro/verify.py"
echo 'PASS delimiter reproducer shows the documented failure'

"$PY" "$ROOT/csv-reduction/make_input.py" "$WORK/big.csv"
"$PY" "$DDMIN" "$WORK/big.csv" \
    --oracle "$PY $ROOT/csv-reduction/parser.py {}" \
    --fail-text 'expected 3 fields, got 4' --output "$WORK/min.csv"
cat "$WORK/min.csv"
[ "$(wc -l <"$WORK/min.csv" | tr -d ' ')" -eq 2 ] ||
    { echo 'FAIL expected two lines' >&2; exit 1; }
grep -q 'Smith, Jr.' "$WORK/min.csv"
# The loose oracle let ddmin replace the real header with row 286; the
# failure text still matched. A stricter oracle keeps the real header.
if grep -q '^id,name,city$' "$WORK/min.csv"; then
    echo 'NOTE loose oracle kept the real header this time'
fi
cat >"$WORK/strict.py" <<PY
import subprocess, sys
text = open(sys.argv[1]).read()
if not text.startswith("id,name,city\\n"):
    sys.exit(0)  # not the failure we are reducing
sys.exit(subprocess.run([sys.executable, "$ROOT/csv-reduction/parser.py",
                         sys.argv[1]]).returncode)
PY
"$PY" "$DDMIN" "$WORK/big.csv" --oracle "$PY $WORK/strict.py {}" \
    --output "$WORK/strict.csv"
head -1 "$WORK/strict.csv" | grep -q '^id,name,city$'
grep -q 'Smith, Jr.' "$WORK/strict.csv"
echo 'PASS ddmin: loose oracle 401 -> 2 lines (stand-in header); strict'
echo '     oracle keeps the real header and the quoted-comma row'

# Some macOS SDK/linker pairs cannot link (ld: tapi error); fall back to the
# first installed SDK that links a trivial program.
pick_sdk() {
    printf 'int main(void){return 0;}\n' >"$WORK/t.c"
    cc "$WORK/t.c" -o "$WORK/t" 2>/dev/null && return 0
    for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.*.sdk; do
        if SDKROOT="$sdk" cc "$WORK/t.c" -o "$WORK/t" 2>/dev/null; then
            export SDKROOT="$sdk"
            echo "NOTE using SDKROOT=$sdk"
            return 0
        fi
    done
    return 1
}
if command -v cc >/dev/null 2>&1 && pick_sdk; then
    cc -g -fsanitize=address -fno-omit-frame-pointer \
        "$ROOT/c-asan/overflow.c" -o "$WORK/overflow"
    status=0
    "$WORK/overflow" 2>"$WORK/asan.log" || status=$?
    [ "$status" -ne 0 ] || { echo 'FAIL ASan did not report' >&2; exit 1; }
    grep -q 'heap-buffer-overflow' "$WORK/asan.log"
    grep -o 'WRITE of size [0-9]*' "$WORK/asan.log" | head -1
    echo 'PASS AddressSanitizer reports the heap-buffer-overflow'
else
    echo 'SKIP c-asan: no C compiler that can link'
fi

status=0
"$PY" "$ROOT/race/counter.py" forced || status=$?
[ "$status" -eq 1 ] || { echo 'FAIL forced race did not reproduce' >&2; exit 1; }
for _ in 1 2 3 4 5; do
    status=0
    "$PY" "$ROOT/race/counter.py" forced || status=$?
    [ "$status" -eq 1 ] || { echo 'FAIL forced race is not reliable' >&2; exit 1; }
done
echo 'PASS forced interleaving reproduces the lost increment 6/6 times'
"$PY" "$ROOT/race/counter.py" rate 200
"$PY" "$ROOT/race/counter.py" fixed
echo 'PASS locked version keeps both increments'
echo 'VERIFY PASSED'
