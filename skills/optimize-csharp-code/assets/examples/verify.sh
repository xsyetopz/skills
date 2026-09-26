#!/usr/bin/env sh
# Builds and runs the construct catalog in a disposable copy so the skill
# directory never receives bin/, obj/, or BenchmarkDotNet artifacts.
#
#   sh verify.sh verify      equivalence + allocation oracles (default)
#   sh verify.sh runtime     print the effective runtime configuration
#   sh verify.sh benchmark   BenchmarkDotNet dry job: harness smoke, no timing
#   sh verify.sh measure     BenchmarkDotNet short job with JSON export
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | runtime | benchmark | measure) ;;
    *)
        echo 'usage: verify.sh [verify|runtime|benchmark|measure]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs/." "$WORK/"
rm -rf "${WORK:?}/bin" "${WORK:?}/obj"
dotnet build "$WORK/Constructs.csproj" -c Release --nologo -v quiet
DLL="$WORK/bin/Release/net10.0/Constructs.dll"
case "$MODE" in
    verify)
        # Allocation oracles need fully optimized code: tier-0 JIT code can
        # box or allocate where the optimized tier does not.
        DOTNET_TieredCompilation=0 dotnet "$DLL" verify
        ;;
    runtime)
        dotnet "$DLL" runtime
        ;;
    benchmark)
        dotnet "$DLL" bench --filter '*' --job dry --artifacts "$WORK/artifacts"
        echo 'SMOKE PASSED: every benchmark ran once; not a timing result.'
        ;;
    measure)
        OUT=${BENCH_OUT:-$PWD/bench-results}
        mkdir -p "$OUT"
        dotnet "$DLL" bench --filter "${BENCH_FILTER:-*}" --job short \
            --exporters json --artifacts "$OUT"
        echo "Results: $OUT/results"
        ;;
esac
