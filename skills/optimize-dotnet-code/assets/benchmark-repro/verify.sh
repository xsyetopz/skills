#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
dotnet build --configuration Release --nologo
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
dotnet ./bin/Release/net10.0/Benchmark.dll red --verify >"$temporary/red"
dotnet ./bin/Release/net10.0/Benchmark.dll green --verify >"$temporary/green"
cmp "$temporary/red" "$temporary/green"
dotnet ./bin/Release/net10.0/Benchmark.dll green
