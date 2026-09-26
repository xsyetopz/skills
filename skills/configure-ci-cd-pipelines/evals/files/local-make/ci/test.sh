#!/usr/bin/env bash
# Runs the unit tests exactly as CI does.
set -euo pipefail
PYTHONPATH=src python3 -m unittest discover -s tests -v "$@"
