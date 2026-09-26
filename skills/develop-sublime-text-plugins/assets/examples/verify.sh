#!/usr/bin/env sh
# Verifies the TodoLens example package in a disposable copy, so no
# __pycache__ or archive is written into the skill directory.
#
#   sh verify.sh          all modes below (default)
#   sh verify.sh offline  pure-core and host-stub suites, snippets compile
#   sh verify.sh mutants  both suites on every mutant in offline/variants.py
#   sh verify.sh py38     py_compile + suites + mutants under Python 3.8
#                         (uv run --python 3.8; SKIP when uv is missing)
#   sh verify.sh check    scripts/check_package.py on the package
#   sh verify.sh package  build TodoLens.sublime-package and list it
#   sh verify.sh host     prints the in-editor UnitTesting command (not run)
#
# PYTHON overrides the interpreter (default python3). A missing tool
# prints SKIP; a check that runs and fails exits 1.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../.." && pwd)
MODE=${1:-all}
case "$MODE" in
    all | offline | mutants | py38 | check | package | host) ;;
    *)
        echo 'usage: verify.sh [all|offline|mutants|py38|check|package|host]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
export PYTHONDONTWRITEBYTECODE=1
cp -R "$ROOT" "$WORK/examples"
OFF="$WORK/examples/offline"
PKG="$WORK/examples/TodoLens"

fail() {
    echo "FAIL $1" >&2
    exit 1
}

suites() { # suites PYTHON...
    for suite in test_core.py test_adapter.py; do
        (cd "$OFF" && "$@" "$suite") >"$WORK/suite.log" 2>&1 || {
            cat "$WORK/suite.log" >&2
            fail "$suite"
        }
        echo "$suite: $(grep -E '^Ran ' "$WORK/suite.log")," \
            "$(tail -n 1 "$WORK/suite.log")"
    done
}

offline() {
    "$PYTHON" --version
    suites "$PYTHON"
    # snippets/ need the editor to run; compile them in memory only.
    n=0
    for f in "$ROOT"/snippets/*.py; do
        "$PYTHON" -c 'import sys; compile(open(sys.argv[1]).read(), "s", "exec")' \
            "$f" || fail "compile $f"
        n=$((n + 1))
    done
    echo "snippets: $n compile"
}

mutants() {
    (cd "$OFF" && "$PYTHON" run_mutants.py) || fail mutants
}

py38() {
    if ! command -v uv >/dev/null 2>&1; then
        echo 'SKIP py38: uv not found'
        return 0
    fi
    set -- uv run --quiet --python 3.8 --no-project python
    "$@" --version
    # py_compile writes __pycache__ even with PYTHONDONTWRITEBYTECODE, so
    # it runs on a second copy that the package check never sees.
    cp -R "$ROOT" "$WORK/compile"
    c="$WORK/compile"
    for f in "$c"/TodoLens/*.py "$c"/TodoLens/tests/*.py \
        "$c"/offline/host_stub/*.py "$c"/snippets/*.py; do
        "$@" -m py_compile "$f" || fail "py_compile 3.8: $f"
    done
    echo 'py_compile 3.8: package, host tests, stub, and snippets compile'
    suites "$@"
    (cd "$OFF" && "$@" run_mutants.py) || fail 'mutants 3.8'
}

check() {
    "$PYTHON" "$SKILL/scripts/check_package.py" "$PKG" \
        --external edit_settings || fail check
}

package() {
    out="$WORK/TodoLens.sublime-package"
    # Archive members sit at the root: no outer TodoLens/ directory. Host
    # tests and unittesting.json stay out of the release archive.
    (cd "$PKG" && "$PYTHON" -m zipfile -c "$out" .python-version \
        core.py plugin.py Context.sublime-menu Default.sublime-commands \
        Default.sublime-keymap TodoLens.sublime-settings)
    "$PYTHON" -m zipfile -l "$out"
    "$PYTHON" - "$out" <<'EOF'
import sys
import zipfile

names = zipfile.ZipFile(sys.argv[1]).namelist()
assert ".python-version" in names and "plugin.py" in names, names
assert not [n for n in names if "/" in n or n.endswith(".pyc")], names
print("archive: %d root-level members, no directories or .pyc" % len(names))
EOF
}

host() {
    echo 'NOT RUNNABLE HERE: needs Sublime Text with UnitTesting installed.'
    echo '  1. Copy TodoLens/ to the Packages directory of a safe-mode or'
    echo '     disposable profile (subl --safe-mode erases its data dir).'
    echo '  2. In the console: window.run_command("unit_testing",'
    echo '     {"package": "TodoLens"})'
}

case "$MODE" in
    offline) offline ;;
    mutants) mutants ;;
    py38) py38 ;;
    check) check ;;
    package) package ;;
    host) host ;;
    all)
        offline
        mutants
        py38
        check
        package
        host
        ;;
esac
echo "VERIFY DONE: $MODE"
