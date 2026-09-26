#!/bin/sh
# Writes N lines (default 20000) of 200 comma-separated 32-character fields.
awk -v n="${1:-20000}" 'BEGIN { x = 7; for (i = 0; i < n; i++) { line = ""; for (j = 0; j < 200; j++) { x = (x * 69069 + 1) % 4294967296; f = sprintf("%032d", x % 50); line = line (j ? "," : "") f } print line } }'
