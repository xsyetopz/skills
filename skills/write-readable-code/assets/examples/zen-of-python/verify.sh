#!/usr/bin/env sh
# Runs every example from the references in a disposable copy.
#
#   sh verify.sh           behavior, mutants, scanner counts, other languages
#   sh verify.sh measure   also times build_index against the immutable form
#
# PYTHON, NODE, GO, RUSTC, JAVAC, JAVA, and CC override the tools. A missing
# tool other than Python is reported as SKIP with the card it leaves
# unverified.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SCAN="$ROOT/../../../scripts/zen_scan.py"
MODE=${1:-verify}
case "$MODE" in
    verify | measure) ;;
    *)
        echo 'usage: verify.sh [verify|measure]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
NODE=${NODE:-node}
GO=${GO:-go}
RUSTC=${RUSTC:-rustc}
JAVAC=${JAVAC:-javac}
JAVA=${JAVA:-java}
CC=${CC:-cc}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/." "$WORK/"
cd "$WORK"
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

have() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    fi
    echo "SKIP $2: '$1' not found"
    return 1
}

# Python: behavior tests, mutants, and the exhaustive before/after pairs.
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" python/test_examples.py >py.log 2>&1 ||
    fail "python tests: $(tail -n 20 py.log)"
ok "python: $(grep -E '^Ran ' py.log) (behavior, mutants, before/after)"
"$PYTHON" -W error::DeprecationWarning -c \
    'import sys; sys.path.insert(0, "python"); import surface; surface.load_config("{}")' ||
    fail "load_config warned"
if "$PYTHON" -W error::DeprecationWarning -c \
    'import sys; sys.path.insert(0, "python"); import surface; surface.read_config("{}")' \
    2>/dev/null; then
    fail "read_config did not warn"
fi
ok "read_config fails under -W error::DeprecationWarning; load_config passes"

# Scanner: 5 findings in the fixture, 0 in the example modules.
status=0
"$PYTHON" "$SCAN" python/zen_before.py >scan.log || status=$?
[ "$status" -eq 1 ] || fail "scanner exit $status on fixture"
grep -q '^5 finding(s)$' scan.log || fail "fixture count: $(cat scan.log)"
for kind in silenced-except broad-except wide-suppress or-default star-import; do
    grep -q ": $kind: " scan.log || fail "fixture misses $kind"
done
ok "zen_scan: fixture has 1 of each of the 5 kinds"
"$PYTHON" "$SCAN" python/explicit_errors.py python/structure.py \
    python/surface.py >clean.log || fail "examples not clean: $(cat clean.log)"
ok "zen_scan: examples report 0 findings"

if [ "$MODE" = measure ]; then
    "$PYTHON" python/test_examples.py measure
fi

# TypeScript: erasable syntax only, run by Node's type stripping.
if have "$NODE" "explicit, sparse/lookup table, namespaces (TypeScript)"; then
    for file in ts/explicit.ts ts/sparse.ts ts/namespaces/main.ts; do
        out=$("$NODE" "langs/$file") || fail "node $file"
        ok "$out"
    done
fi

# Go: error wrapping, retry policy, one exported constructor, gofmt.
if have "$GO" "specific errors, complex not complicated, one obvious way (Go)"; then
    cd langs/go
    ok "$("$GO" run ./errors | tail -n 1)"
    ok "$("$GO" run ./retry)"
    "$GO" test ./surface >/dev/null || fail "go test ./surface"
    exported=$("$GO" doc -short ./surface | grep -c 'func ')
    [ "$exported" -eq 1 ] || fail "expected 1 exported func, got $exported"
    ok "surface: go test passes; go doc lists 1 exported constructor"
    [ -z "$(gofmt -l errors retry surface)" ] || fail "gofmt -l lists files"
    [ -n "$(gofmt -l unformatted/add.go.txt)" ] || fail "gofmt missed fixture"
    ok "gofmt -l: examples clean, unformatted fixture listed"
    cd "$WORK"
fi

# Rust: silence exactly NotFound; refuse a duration without a unit.
if have "$RUSTC" "explicitly silenced, refuse to guess (Rust)"; then
    "$RUSTC" --edition 2021 -o explicit langs/rust/explicit.rs 2>rustc.log ||
        fail "rustc: $(cat rustc.log)"
    ./explicit >rust.log || fail "rust example"
    while IFS= read -r line; do ok "$line"; done <rust.log
fi

# Java: same output from 1 class as from the 4-class hierarchy.
if have "$JAVAC" "simple is better than complex (Java)" &&
    have "$JAVA" "simple is better than complex (Java)"; then
    mkdir -p classes
    "$JAVAC" -d classes langs/java/SimpleBefore.java langs/java/SimpleAfter.java
    ok "$("$JAVA" -cp classes SimpleAfter)"
    before=$(find classes -name 'SimpleBefore*.class' | wc -l | tr -d ' ')
    after=$(find classes -name 'SimpleAfter*.class' | wc -l | tr -d ' ')
    [ "$before" -eq 4 ] && [ "$after" -eq 1 ] ||
        fail "class counts $before/$after"
    ok "class files: before $before, after $after"
fi

# C: flat and nested decisions agree on every input.
build_c() {
    "$CC" -std=c11 -Wall -Wextra -Werror -o flat langs/c/flat.c 2>cc.log
}
if have "$CC" "guard clauses / flat is better than nested (C)"; then
    if ! build_c && [ "$(uname -s)" = Darwin ]; then
        # Some macOS SDKs fail to link (ld: tapi error); retry older SDKs.
        for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX2*.sdk \
            /Library/Developer/CommandLineTools/SDKs/MacOSX1*.sdk; do
            [ -d "$sdk" ] || continue
            SDKROOT=$sdk build_c && break
        done
    fi
    [ -x flat ] || fail "cc: $(cat cc.log)"
    ok "$(./flat)"
    depth() {
        awk -v fn="$1" '
            $0 ~ "^static enum status " fn "\\(" { inside = 1 }
            inside {
                d -= gsub(/}/, "}")
                if (d == 0 && max > 0) { print max - 1; exit }
                d += gsub(/{/, "{"); if (d > max) max = d
            }' langs/c/flat.c
    }
    nested=$(depth decide_nested)
    flat=$(depth decide)
    [ "$nested" -eq 3 ] && [ "$flat" -eq 1 ] || fail "depths $nested/$flat"
    ok "brace depth inside function: nested $nested, flat $flat"
fi

echo "$PASS checks passed"
