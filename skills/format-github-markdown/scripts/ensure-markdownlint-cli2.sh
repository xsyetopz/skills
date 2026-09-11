#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname -- "$SCRIPT_DIR")"
SOURCE="$SKILL_DIR/assets/.markdownlint-cli2.jsonc"

if [[ $# -gt 1 ]]; then
  printf 'usage: %s [repo-root]\n' "$0" >&2
  exit 64
fi

if [[ $# -eq 1 ]]; then
  ROOT="$(CDPATH='' cd -- "$1" && pwd)"
elif ROOT_GIT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  ROOT="$ROOT_GIT"
else
  ROOT="$PWD"
fi

for name in \
  .markdownlint-cli2.jsonc \
  .markdownlint-cli2.yaml \
  .markdownlint-cli2.cjs \
  .markdownlint-cli2.mjs \
  .markdownlint.jsonc \
  .markdownlint.json \
  .markdownlint.yaml \
  .markdownlint.yml \
  .markdownlint.cjs \
  .markdownlint.mjs; do
  if [[ -e "$ROOT/$name" || -L "$ROOT/$name" ]]; then
    printf '%s\n' "$ROOT/$name"
    exit 0
  fi
done

if [[ -e "$ROOT/.markdownlint-cli2.json" || -L "$ROOT/.markdownlint-cli2.json" ]]; then
  printf '%s\n' 'Existing .markdownlint-cli2.json is not auto-discovered; review its configuration name before installation.' >&2
  exit 1
fi

install -m 0644 "$SOURCE" "$ROOT/.markdownlint-cli2.jsonc"
printf '%s\n' "$ROOT/.markdownlint-cli2.jsonc"
