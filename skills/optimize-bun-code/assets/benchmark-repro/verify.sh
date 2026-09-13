#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
bun bench.ts red --verify >"$temporary/red"
bun bench.ts green --verify >"$temporary/green"
cmp "$temporary/red" "$temporary/green"
bun bench.ts green
