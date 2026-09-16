#!/usr/bin/env sh
set -eu
[ "$#" -eq 0 ] || { echo 'usage: verify.sh' >&2; exit 2; }
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v iverilog >/dev/null || { echo 'requires iverilog' >&2; exit 2; }
command -v vvp >/dev/null || { echo 'requires vvp' >&2; exit 2; }
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
for implementation in counter counter_equivalent counter_faulty; do
    iverilog -g2012 -s counter_tb -o "$WORK/test"       "$ROOT/$implementation.sv" "$ROOT/counter_tb.sv"
    status=0
    vvp "$WORK/test" >"$WORK/result" 2>&1 || status=$?
    cat "$WORK/result"
    if [ "$implementation" = counter_faulty ]; then
        [ "$status" -ne 0 ] || { echo 'fault was not rejected' >&2; exit 1; }
        grep -q 'CONTRACT FAIL: expected=15 observed=0' "$WORK/result" || {
            echo 'fault failed for a different reason' >&2; exit 1;
        }
    else
        [ "$status" -eq 0 ] || exit "$status"
        grep -q '^CONTRACT PASS$' "$WORK/result" || {
            echo 'assertions did not complete' >&2; exit 1;
        }
    fi
done
