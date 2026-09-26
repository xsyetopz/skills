#!/usr/bin/env sh
# Runs the construct catalog in a disposable copy so the skill directory
# never receives __pycache__ or pyperf output.
#
#   sh verify.sh verify     equivalence + deterministic benefit oracles
#                           (stdlib only; default)
#   sh verify.sh benchmark  pyperf --debug-single-value smoke for both
#                           variants; harness check, not a timing result
#   sh verify.sh measure    pyperf timing for both variants, JSON under
#                           BENCH_OUT (default ./bench-results), then
#                           compare_to --table; BENCH_FILTER picks pairs,
#                           PYPERF_ARGS adds options (for example --fast)
#
# PYTHON selects the interpreter (default python3); benchmark and measure
# need pyperf importable by it.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | measure) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|measure]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs/." "$WORK/"
rm -rf "$WORK/__pycache__"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON" -VV
case "$MODE" in
    verify)
        "$PYTHON" "$WORK/main.py" verify
        ;;
    benchmark)
        for variant in baseline candidate; do
            "$PYTHON" "$WORK/bench.py" --variant "$variant" \
                --filter "${BENCH_FILTER:-}" --debug-single-value --quiet
        done
        echo 'SMOKE PASSED: every pair ran once; not a timing result.'
        ;;
    measure)
        OUT=${BENCH_OUT:-$PWD/bench-results}
        mkdir -p "$OUT"
        for variant in baseline candidate; do
            rm -f "$OUT/$variant.json"
            # shellcheck disable=SC2086 # PYPERF_ARGS is a word list
            "$PYTHON" "$WORK/bench.py" --variant "$variant" \
                --filter "${BENCH_FILTER:-}" -o "$OUT/$variant.json" \
                ${PYPERF_ARGS:-}
        done
        "$PYTHON" -m pyperf compare_to "$OUT/baseline.json" \
            "$OUT/candidate.json" --table
        echo "Results: $OUT"
        ;;
esac
