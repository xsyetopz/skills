#!/usr/bin/env bash
# Formats the file Claude just edited.
set -euo pipefail
file=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["tool_input"].get("file_path", ""))')
case "$file" in
  *.ts|*.js) npx --no-install prettier --write "$file" >/dev/null 2>&1 || true ;;
esac
