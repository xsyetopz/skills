#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo build --release --locked
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
./target/release/rust-skill-benchmark red --verify >"$temporary/red"
./target/release/rust-skill-benchmark green --verify >"$temporary/green"
cmp "$temporary/red" "$temporary/green"
./target/release/rust-skill-benchmark green
