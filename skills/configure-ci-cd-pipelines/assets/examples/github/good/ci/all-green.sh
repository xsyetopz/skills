#!/usr/bin/env bash
# Required-check aggregator: exit 0 only when every required job
# succeeded, or was skipped where skipping is the intended behavior.
# Usage: all-green.sh EVENT TEST_RESULT TITLE_RESULT
set -euo pipefail
event=$1 test=$2 title=$3
fail=0
if [ "$test" != success ]; then
    echo "test: $test (required: success)"
    fail=1
fi
if [ "$event" = pull_request ]; then
    expected_title=success
else
    expected_title=skipped # pr-title runs only for pull requests
fi
if [ "$title" != "$expected_title" ]; then
    echo "pr-title: $title (required: $expected_title)"
    fail=1
fi
exit "$fail"
