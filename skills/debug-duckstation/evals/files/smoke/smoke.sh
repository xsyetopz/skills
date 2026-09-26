#!/bin/sh
# Nightly smoke test: boot the test disc and check DuckStation exits cleanly.
DS=/Applications/DuckStation.app/Contents/MacOS/DuckStation
"$DS" -batch -nogui -portable -- "$HOME/ci/test.cue" > run.log 2>&1
status=$?
if [ "$status" -ne 0 ]; then
  echo "SMOKE FAIL: DuckStation exited $status"
  exit 1
fi
echo "SMOKE PASS"
