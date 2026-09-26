#!/usr/bin/env sh
# Offline checks (default) and an opt-in check of the official release binary.
#
#   verify.sh          script tests and format fixtures; offline, a few seconds
#   verify.sh release  macOS only; downloads the official v0.1-11826 macOS
#                      zip (about 91 MB) from GitHub releases, then runs it in
#                      portable mode for about 30 s. It may open a DuckStation
#                      window. It uses no BIOS or game image.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../.." && pwd)
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
MODE=${1:-offline}

offline() {
    log=$(mktemp)
    for t in "$SKILL"/scripts/test_*.py; do
        "$PY" "$t" >"$log" 2>&1 || { cat "$log"; rm -f "$log"; exit 1; }
        tail -1 "$log"
    done
    rm -f "$log"
    "$PY" "$SKILL/scripts/check_formats.py" settings \
        "$ROOT/settings/debug-overlay.ini"
    "$PY" "$SKILL/scripts/check_formats.py" cht "$ROOT/cheats/HASH-EXAMPLE.cht"
    # shellcheck disable=SC2046
    "$PY" "$SKILL/scripts/check_formats.py" texture-name \
        $(cat "$ROOT/textures/names.txt")
    for bad in settings:settings/bad-overlay.ini cht:cheats/bad-example.cht; do
        if "$PY" "$SKILL/scripts/check_formats.py" "${bad%%:*}" \
            "$ROOT/${bad#*:}" >/dev/null; then
            echo "FAIL negative fixture ${bad#*:} passed" >&2
            exit 1
        fi
    done
    echo 'PASS offline: script tests, good fixtures OK, bad fixtures rejected'
}

run_for() {
    # run_for SECONDS LOGFILE ARGS...: start, wait, then stop the process.
    seconds=$1 out=$2
    shift 2
    "$@" >"$out" 2>&1 &
    pid=$!
    sleep "$seconds"
    if kill -0 "$pid" 2>/dev/null; then
        echo "process $pid still running after ${seconds}s"
        LAST_PID=$pid
    else
        LAST_PID=
        wait "$pid" || echo "process exited with status $?"
    fi
}

stop_last() {
    [ -n "${LAST_PID:-}" ] || return 0
    kill "$LAST_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$LAST_PID" 2>/dev/null || true
}

release() {
    [ "$(uname -s)" = Darwin ] || { echo 'SKIP release: macOS only'; return; }
    tag=v0.1-11826
    sum=1870ef7c34f619861cf9bedfe73772cb2106061058ce6e40a7b41dc328835a96
    url=https://github.com/stenzek/duckstation/releases/download/$tag
    work=$(mktemp -d)
    trap 'stop_last; rm -rf "$work"' 0
    curl -fsSL -o "$work/ds.zip" "$url/duckstation-mac-release.zip"
    echo "$sum  $work/ds.zip" | shasum -a 256 -c -
    ditto -x -k "$work/ds.zip" "$work/case"
    macos="$work/case/DuckStation.app/Contents/MacOS"
    bin="$macos/DuckStation"
    touch "$macos/portable.txt"

    status=0
    "$bin" -help 2>"$work/help.txt" >/dev/null || status=$?
    echo "-help exit status $status (0.1-11826 prints to stderr, exits 1)"
    grep '^  -' "$work/help.txt" >"$work/flags.now"
    grep '^  -' "$ROOT/help-0.1-11826.txt" >"$work/flags.fixture"
    diff "$work/flags.fixture" "$work/flags.now"
    echo 'PASS -help lists the same flags as the bundled fixture'

    user="$HOME/Library/Application Support/DuckStation"
    before=$(stat -f %m "$user" 2>/dev/null || echo absent)
    printf 'not a PS-X EXE\n' >"$work/dummy.exe"
    run_for 12 "$work/run1.txt" "$bin" -batch -nogui -- "$work/dummy.exe"
    stop_last
    test -f "$macos/settings.ini"
    "$PY" "$SKILL/scripts/check_formats.py" settings "$macos/settings.ini"
    "$PY" - "$macos/settings.ini" "$ROOT/settings/keys-0.1-11826.txt" <<'EOF'
import sys
written, section = [], ""
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if line.startswith("["):
        section = line[1:-1]
    elif "=" in line:
        key, value = (part.strip() for part in line.split("=", 1))
        written.append(f"{section}.{key}\t{value}")
fixture = set(open(sys.argv[2], encoding="utf-8").read().splitlines())
extra = [pair for pair in written if pair not in fixture]
if extra:
    sys.exit(f"FAIL keys or defaults not in the bundled list: {extra[:5]}")
# Main.SetupWizardIncomplete was written in some first runs only.
print(f"PASS {len(written)} first-run keys and defaults are in the list")
EOF
    echo 'PASS portable: settings.ini written next to the executable'

    sed -i '' -e 's/^LogToFile = false/LogToFile = true/' \
        -e 's/^LogLevel = Info/LogLevel = Debug/' "$macos/settings.ini"
    run_for 12 "$work/run2.txt" "$bin" -batch -nogui -- "$work/dummy.exe"
    if [ -n "$LAST_PID" ] && command -v lldb >/dev/null 2>&1; then
        lldb --batch -p "$LAST_PID" -o 'bt' -o 'detach' >"$work/lldb.txt" 2>&1
        grep -q 'DuckStation`main' "$work/lldb.txt"
        echo 'PASS lldb attached to the release process and printed main'
    fi
    stop_last
    grep -m1 'I/Core: Version:' "$macos/duckstation.log"
    # Boot progress lines (Boot Path, BIOS search) appeared in some runs
    # only, so they are printed, not asserted.
    grep -m2 -E 'I/System: Boot Path|I/BIOS: Searching' \
        "$macos/duckstation.log" || echo 'no boot line logged this run'
    echo 'PASS log file written next to the executable'
    find "$HOME/Library/Logs/DiagnosticReports" -name 'DuckStation-*.ips' \
        -newer "$work/ds.zip" 2>/dev/null | sed 's/^/crash report: /'

    after=$(stat -f %m "$user" 2>/dev/null || echo absent)
    [ "$before" = "$after" ] || { echo "FAIL $user changed" >&2; exit 1; }
    echo "PASS default user directory untouched ($after)"
}

case $MODE in
    offline) offline ;;
    release) offline; release ;;
    *) echo "usage: $0 [offline|release]" >&2; exit 2 ;;
esac
echo 'VERIFY PASSED'
