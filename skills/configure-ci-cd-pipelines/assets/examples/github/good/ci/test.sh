#!/usr/bin/env bash
# Stand-in for the project's test command; prints the interpreter version.
set -euo pipefail
echo "testing with python ${1:?python version}"
