#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo build --release --locked
red=$(./target/release/rust-skill-benchmark red)
green=$(./target/release/rust-skill-benchmark green)
test "$red" = "$green"
printf '%s\n' "$green"
