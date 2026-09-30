#!/bin/sh
# Runs one headless Claude Code job per line of jobs.txt.
mkdir -p out
n=0
while IFS= read -r job; do
  n=$((n + 1))
  claude -p "$job" --output-format json > "out/run-$n.json"
done < jobs.txt
