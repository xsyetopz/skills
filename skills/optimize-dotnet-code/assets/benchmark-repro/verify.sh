#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
dotnet build --configuration Release --nologo
red=$(dotnet ./bin/Release/net10.0/Benchmark.dll red)
green=$(dotnet ./bin/Release/net10.0/Benchmark.dll green)
test "$red" = "$green"
printf '%s\n' "$green"
