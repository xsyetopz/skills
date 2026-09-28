#!/usr/bin/env sh
# Runs the construct oracles in a disposable copy so the skill directory
# never receives emitted JavaScript, .tsbuildinfo, traces, or node_modules.
#
#   sh verify.sh verify     emit + checker oracles (default)
#   sh verify.sh emit       emit/runtime-semantics oracles only
#   sh verify.sh checker    type-checker and build oracles only
#   sh verify.sh benchmark  same as verify; smoke only, no timing
#   sh verify.sh measure    oracles, then machine-specific timings
#   sh verify.sh trace      --generateTrace + @typescript/analyze-trace
#
# tsc: TSC if set, else ./node_modules/.bin/tsc under the current
# directory, else tsc on PATH. Needs Node 22.18+ (type stripping on by
# default). Bun is optional: it installs tslib@2.8.1 for the importHelpers
# case (network on a cache miss) and runs the Bun cases.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | emit | checker | benchmark | measure | trace) ;;
    *)
        echo 'usage: verify.sh [verify|emit|checker|benchmark|measure|trace]' >&2
        exit 2
        ;;
esac
if [ -z "${TSC:-}" ]; then
    if [ -x "$PWD/node_modules/.bin/tsc" ]; then
        TSC="$PWD/node_modules/.bin/tsc"
    else
        TSC=$(command -v tsc) || {
            echo 'tsc not found; set TSC=/path/to/tsc' >&2
            exit 2
        }
    fi
fi
case "$TSC" in
    /*) ;;
    */*) TSC="$PWD/$TSC" ;;
esac
export TSC
node -e 'const [a, b] = process.versions.node.split(".").map(Number);
process.exit(a > 22 || (a === 22 && b >= 18) ? 0 : 1)' || {
    echo "Node 22.18+ is required (type stripping); found $(node -v)" >&2
    exit 2
}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/." "$WORK/"
rm -f "$WORK/verify.sh"
cd "$WORK"
if command -v bun >/dev/null 2>&1 && [ "$MODE" != checker ]; then
    bun add --exact tslib@2.8.1 >/dev/null 2>&1 ||
        echo 'tslib install failed; importHelpers case will be skipped' >&2
fi
case "$MODE" in
    benchmark)
        node harness.ts verify
        echo 'SMOKE PASSED: oracles only; not a timing result.'
        ;;
    trace)
        node harness.ts checker >/dev/null
        "$TSC" gen/union.ts --noEmit --skipLibCheck --singleThreaded \
            --generateTrace trace-out
        bunx --bun @typescript/analyze-trace@0.11.1 trace-out \
            --forceMillis 50 --skipMillis 5 --color false || [ $? -eq 1 ]
        ;;
    *)
        node harness.ts "$MODE"
        ;;
esac
