#!/usr/bin/env sh
# Runs the Go construct catalog in a disposable copy so the skill directory
# never receives test binaries, profiles, or default.pgo files.
#
#   sh verify.sh verify       vet + equivalence and allocation oracles
#   sh verify.sh race         equivalence oracles under the race detector
#   sh verify.sh diagnostics  escape, inlining, and bounds-check assertions
#   sh verify.sh benchmark    every benchmark once (-benchtime 1x): smoke only
#   sh verify.sh measure      -count 10 benchmarks, then benchstat -col /impl
#   sh verify.sh profile      CPU/heap profiles and an execution trace
#   sh verify.sh pgo          build with and without a generated default.pgo
#
# Environment: BENCH_FILTER (default .), BENCH_COUNT (default 10),
# BENCH_OUT (default ./bench-results), BENCHSTAT (benchstat command).
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | race | diagnostics | benchmark | measure | profile | pgo) ;;
    *)
        echo 'usage: verify.sh [verify|race|diagnostics|benchmark|measure|profile|pgo]' >&2
        exit 2
        ;;
esac
OUT=${BENCH_OUT:-$PWD/bench-results}
FILTER=${BENCH_FILTER:-.}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs/." "$WORK/"
cd "$WORK"
export GOTOOLCHAIN=local
go version

# expect NAME eq|ge N PATTERN FILE: assert that the number of lines of FILE
# matching PATTERN is equal to (eq) or at least (ge) N.
expect() {
    got=$(grep -c -- "$4" "$5" || true)
    if { [ "$2" = eq ] && [ "$got" -eq "$3" ]; } ||
        { [ "$2" = ge ] && [ "$got" -ge "$3" ]; }; then
        echo "PASS $1 ($got matching lines)"
    else
        echo "FAIL $1: $got lines match '$4', want $2 $3" >&2
        exit 1
    fi
}

case "$MODE" in
    verify)
        go vet ./...
        status=0
        go test -count 1 -v ./... >"$WORK/test.txt" 2>&1 || status=$?
        grep -E 'ALLOCS|GC cycles|calls|started|Event|total|^(ok|FAIL|---)' \
            "$WORK/test.txt" || true
        [ "$status" -eq 0 ] || cat "$WORK/test.txt" >&2
        exit "$status"
        ;;
    race)
        go test -race -count 1 ./...
        ;;
    diagnostics)
        go build -gcflags=-m . 2>"$WORK/m.txt"
        expect 'escape baseline heap' ge 1 \
            'escape_baseline.go.*&Header{...} escapes to heap' "$WORK/m.txt"
        expect 'escape candidate stack' eq 0 \
            'escape_candidate.go.*escapes to heap' "$WORK/m.txt"
        go build -gcflags=-m=2 . 2>"$WORK/m2.txt"
        expect 'inline baseline over budget' eq 1 \
            'cannot inline (\*Reader).Uint16Baseline: function too complex' \
            "$WORK/m2.txt"
        expect 'inline candidate inlinable' eq 1 \
            'can inline (\*Reader).Uint16Candidate' "$WORK/m2.txt"
        grep -E 'inline \(\*Reader\)\.Uint16' "$WORK/m2.txt" | cut -c1-120
        go build -gcflags=-d=ssa/check_bce/debug=1 . 2>"$WORK/bce.txt"
        expect 'bce baseline check' ge 1 'bce_baseline.go.*Found IsInBounds' \
            "$WORK/bce.txt"
        expect 'bce candidate no check' eq 0 'bce_candidate.go.*Found' \
            "$WORK/bce.txt"
        ;;
    benchmark)
        go test -run '^$' -bench "$FILTER" -benchtime 1x -benchmem .
        echo 'SMOKE PASSED: every benchmark ran once; not a timing result.'
        ;;
    measure)
        mkdir -p "$OUT"
        go test -run '^$' -bench "$FILTER" -benchmem \
            -count "${BENCH_COUNT:-10}" . >"$OUT/bench.txt"
        cat "$OUT/bench.txt"
        if [ -n "${BENCHSTAT:-}" ]; then
            # shellcheck disable=SC2086 # BENCHSTAT may be a command line.
            $BENCHSTAT -col /impl "$OUT/bench.txt"
        elif command -v benchstat >/dev/null 2>&1; then
            benchstat -col /impl "$OUT/bench.txt"
        else
            echo "benchstat not found; raw results: $OUT/bench.txt"
        fi
        ;;
    profile)
        mkdir -p "$OUT"
        go test -run '^$' -bench "$FILTER" -benchmem -count 1 \
            -cpuprofile "$OUT/cpu.pprof" -memprofile "$OUT/mem.pprof" \
            -o "$OUT/constructs.test" .
        go tool pprof -top -nodecount 15 "$OUT/constructs.test" \
            "$OUT/cpu.pprof"
        go tool pprof -top -nodecount 15 -sample_index=alloc_space \
            "$OUT/constructs.test" "$OUT/mem.pprof"
        go test -run '^$' -bench "$FILTER" -benchtime 100x \
            -trace "$OUT/trace.out" .
        echo "Profiles: $OUT; view the trace with: go tool trace $OUT/trace.out"
        ;;
    pgo)
        go build -pgo=off -o "$WORK/nopgo" ./cmd/pgodemo
        "$WORK/nopgo" -cpuprofile "$WORK/cmd/pgodemo/default.pgo" >/dev/null
        go build -o "$WORK/withpgo" ./cmd/pgodemo
        go version -m "$WORK/withpgo" >"$WORK/buildinfo.txt"
        expect 'pgo build setting' eq 1 '-pgo=.*default.pgo' \
            "$WORK/buildinfo.txt"
        go build -pgo=off -gcflags=-m=2 ./cmd/pgodemo 2>"$WORK/off.txt"
        go build -gcflags=-m=2 ./cmd/pgodemo 2>"$WORK/on.txt"
        expect 'no PGO devirtualization without a profile' eq 0 \
            'PGO devirtualizing' "$WORK/off.txt"
        expect 'Next over budget without a profile' eq 1 \
            'cannot inline fieldTokenizer.Next: function too complex' \
            "$WORK/off.txt"
        expect 'PGO devirtualizes tok.Next' eq 1 \
            'PGO devirtualizing interface call tok.Next' "$WORK/on.txt"
        expect 'PGO inlines hot Next over budget' eq 1 \
            'can inline fieldTokenizer.Next with cost' "$WORK/on.txt"
        grep -hE 'PGO devirtualizing|inline fieldTokenizer.Next' \
            "$WORK/off.txt" "$WORK/on.txt" | cut -c1-120
        ;;
esac
