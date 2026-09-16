#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../comparisons"
# Build once; run each command under the same independent measurement harness.
# These are comparisons, NOT a recommendation to override the runtime defaults.
test -f bin/Release/net10.0/Pairs.dll || {
  echo 'Build once first: dotnet build Pairs.csproj -c Release' >&2
  exit 1
}
case "${1:-}" in
  pgo-on) DOTNET_TieredCompilation=1 DOTNET_TieredPGO=1 dotnet bin/Release/net10.0/Pairs.dll candidate 4 10000 ;;
  pgo-off) DOTNET_TieredCompilation=1 DOTNET_TieredPGO=0 dotnet bin/Release/net10.0/Pairs.dll candidate 4 10000 ;;
  *) echo 'usage: runtime-experiments.sh pgo-on|pgo-off' >&2; exit 1 ;;
esac
# This short-lived CLI is a STARTUP workload; it cannot establish warmed-service PGO behavior.
