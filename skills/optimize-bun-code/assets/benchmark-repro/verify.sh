#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
red=$(bun bench.ts red)
green=$(bun bench.ts green)
test "$red" = "$green"
printf '%s\n' "$green"
