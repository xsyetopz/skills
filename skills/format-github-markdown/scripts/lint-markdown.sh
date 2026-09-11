#!/usr/bin/env bash
set -euo pipefail

VERSION="${MARKDOWNLINT_CLI2_VERSION:-0.23.2}"

if command -v bunx >/dev/null 2>&1; then
  exec bunx --yes "markdownlint-cli2@$VERSION" "$@"
fi

printf '%s\n' \
  'bunx is unavailable; install Bun to run markdownlint-cli2.' >&2
exit 127
