#!/usr/bin/env sh
# Runs the construct catalog in a disposable copy so the skill directory
# never receives profiles, snapshots, or node_modules.
#
#   sh verify.sh verify     oracles + benefit assertions on node and bun,
#                           V8 and JSC probes, deopt trace (default)
#   sh verify.sh benchmark  harness smoke: every pair runs once; no timing
#   sh verify.sh measure    timed pairs with the bundled harness
#                           (BENCH_FILTER=substring narrows the pairs)
#   sh verify.sh profile    --cpu-prof, --heap-prof, heap snapshot, and
#                           sampling allocation profile checks
#   sh verify.sh mitata     installs mitata@1.0.34 (network) and runs it
#
# NODE and BUN override the runtimes. A missing bun is reported as SKIP.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | measure | profile | mitata) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|measure|profile|mitata]' >&2
        exit 2
        ;;
esac
NODE=${NODE:-node}
BUN=${BUN:-bun}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs/." "$WORK/"
cd "$WORK"

have_bun() {
    if command -v "$BUN" >/dev/null 2>&1; then
        return 0
    fi
    echo "SKIP bun: '$BUN' not found; JavaScriptCore results not verified"
    return 1
}

case "$MODE" in
    verify)
        "$NODE" --expose-gc run.mjs verify
        "$NODE" --allow-natives-syntax v8-probes.mjs
        if "$NODE" --trace-deopt deopt.mjs | grep -q 'reason: not a Smi'; then
            echo 'PASS deopt: add() deoptimized on a string argument'
        else
            echo 'FAIL deopt: expected a "not a Smi" bailout' >&2
            exit 1
        fi
        if "$NODE" --trace-deopt deopt.mjs stable |
            grep -q 'bailout.*<JSFunction add '; then
            echo 'FAIL deopt: stable variant still deoptimized add()' >&2
            exit 1
        fi
        echo 'PASS deopt: stable variant kept add() optimized'
        if have_bun; then
            "$BUN" run.mjs verify
            "$BUN" jsc-probes.mjs
            "$BUN" bun-io.mjs
        fi
        ;;
    benchmark)
        "$NODE" run.mjs benchmark
        if have_bun; then "$BUN" run.mjs benchmark; fi
        ;;
    measure)
        "$NODE" run.mjs measure "${BENCH_FILTER:-}"
        if have_bun; then "$BUN" run.mjs measure "${BENCH_FILTER:-}"; fi
        ;;
    profile)
        "$NODE" --cpu-prof --cpu-prof-dir=prof workload.mjs
        "$NODE" --heap-prof --heap-prof-dir=prof workload.mjs
        "$NODE" -e 'require("v8").writeHeapSnapshot("prof/app.heapsnapshot")'
        "$NODE" check-profiles.mjs prof
        "$NODE" alloc-profile.mjs
        if have_bun; then
            rm -rf prof
            "$BUN" --cpu-prof --cpu-prof-dir=prof workload.mjs
            "$NODE" check-profiles.mjs prof
        fi
        ;;
    mitata)
        # bun installs the package; without bun this mode cannot run.
        if ! have_bun; then exit 0; fi
        echo '{"private":true}' >package.json
        "$BUN" add mitata@1.0.34
        "$NODE" mitata-bench.mjs "${BENCH_FILTER:-}"
        "$BUN" mitata-bench.mjs "${BENCH_FILTER:-}"
        ;;
esac
