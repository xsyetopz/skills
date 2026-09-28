#!/bin/sh
# Keep Codex working until the unit tests pass.
cd "$(git rev-parse --show-toplevel)" || exit 0
if ! python3 -m unittest -q >/dev/null 2>&1; then
  echo "tests failed, keep going"
fi
exit 0
