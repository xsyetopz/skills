#!/bin/sh
# Writes N deterministic whitespace-separated longs (default 2000000) to stdout.
awk -v n="${1:-2000000}" 'BEGIN { x = 12345; for (i = 0; i < n; i++) { x = (x * 69069 + 1) % 4294967296; printf "%d%s", x - 2147483648, (i % 16 == 15) ? "\n" : " " } }'
