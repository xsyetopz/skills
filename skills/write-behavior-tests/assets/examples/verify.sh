#!/usr/bin/env sh
# Runs the examples behind every card in a disposable copy.
#
#   sh verify.sh           offline: variant matrix, observed red/green,
#                          mutation runs, Go corpus, HDL (if iverilog)
#   sh verify.sh network   also Hypothesis properties and the wheel
#                          install test (downloads pinned packages via uv)
#   sh verify.sh fuzz      also 10 s of Go coverage-guided fuzzing
#
# PYTHON, GO, and UV override the tools.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MUTATE="$ROOT/../../scripts/mutate.py"
MODE=${1:-verify}
case "$MODE" in
    verify | network | fuzz) ;;
    *)
        echo 'usage: verify.sh [verify|network|fuzz]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
GO=${GO:-go}
UV=${UV:-uv}
HYPOTHESIS=hypothesis==6.168.1
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/." "$WORK/"
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

cd "$WORK/behavior"

# 1. Every good suite passes the reference and the alternatives, fails the
#    exact tests named for each mutant; weak tests miss their mutants.
"$PYTHON" run_matrix.py >matrix.log || fail "matrix: $(grep -v '^ok' matrix.log)"
ok "variant matrix: $(tail -n 1 matrix.log)"

# 2. Observed red for the intended reason, then green.
status=0
VARIANT=bug_split_drops_empty "$PYTHON" -m unittest \
    test_regressions.SplitRegressionTests >red.log 2>&1 || status=$?
[ "$status" -ne 0 ] || fail "regression test passed on the faulty version"
grep -q "AssertionError: Lists differ" red.log || fail "red for wrong reason"
if grep -qE 'ImportError|ModuleNotFoundError|NameError' red.log; then
    fail "red caused by setup"
fi
ok "red: faulty split fails with AssertionError: Lists differ"
"$PYTHON" -m unittest test_regressions.SplitRegressionTests >green.log 2>&1 ||
    fail "green run"
ok "green: reference split passes the same test"

# 3. Mutation: the weak test leaves a survivor, the full suite kills it.
status=0
"$PYTHON" "$MUTATE" subjects.py --function write_config \
    --test "$PYTHON -m unittest -q weak_examples.WeakWriteConfig" \
    >weak-mut.log || status=$?
[ "$status" -eq 1 ] || fail "weak mutation exit $status"
grep -q 'arith: Add -> Sub: survived' weak-mut.log || fail "no survivor"
ok "mutate + weak test: $(tail -n 1 weak-mut.log)"
"$PYTHON" "$MUTATE" subjects.py --function write_config \
    --test "$PYTHON -m unittest -q test_regressions" >mut.log ||
    fail "survivors with full suite: $(cat mut.log)"
ok "mutate + full suite: $(tail -n 1 mut.log)"
"$PYTHON" "$MUTATE" subjects.py --function accept_percentage \
    --function can_edit --function next_state \
    --test "$PYTHON -m unittest -q test_oracles" >oracle-mut.log ||
    fail "oracle survivors: $(grep survived oracle-mut.log)"
ok "mutate oracles: $(tail -n 1 oracle-mut.log)"

"$PYTHON" -m unittest test_architecture >arch.log 2>&1 || fail "$(cat arch.log)"
ok "architecture rule: subjects.py imports no test module; probe detected"

# 4. Native instrumentation: plain run exits 0, ASan reports the write.
cd "$WORK/c"
CC=${CC:-cc}
build_c() {
    "$CC" -g -O0 "$@" -o overflow overflow.c 2>cc.log && return 0
    [ "$(uname -s)" = Darwin ] || return 1
    # Some macOS SDKs fail to link (ld: tapi error); retry installed SDKs.
    for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.sdk; do
        [ -d "$sdk" ] || continue
        SDKROOT=$sdk "$CC" -g -O0 "$@" -o overflow overflow.c 2>cc.log && return 0
    done
    return 1
}
if command -v "$CC" >/dev/null 2>&1 && build_c; then
    ./overflow >plain.log 2>&1 || fail "plain run failed"
    ok "plain build: off-by-one write exits 0 ($(cat plain.log))"
    build_c -fsanitize=address || fail "asan build: $(cat cc.log)"
    if sh -c ./overflow >asan.log 2>&1; then
        fail "asan did not report"
    fi
    grep -q 'heap-buffer-overflow' asan.log || fail "unexpected asan report"
    grep -q 'in fill overflow.c:7' asan.log || fail "asan frame"
    ok "asan: heap-buffer-overflow, WRITE in fill overflow.c:7"
else
    echo "SKIP sanitizer card: no working C compiler"
fi

# 5. Go: committed fuzz corpus replays as regression tests.
cd "$WORK/go"
if command -v "$GO" >/dev/null 2>&1; then
    "$GO" vet ./... || fail "go vet"
    "$GO" test ./escape >go.log 2>&1 || fail "go test: $(cat go.log)"
    ok "go test: unit test and 2 corpus entries pass on the fixed build"
    if "$GO" test -tags bug -run FuzzUnquote ./escape >bug.log 2>&1; then
        fail "bug build passed the corpus"
    fi
    grep -q 'FuzzUnquote/trailing-backslash' bug.log || fail "wrong corpus failure"
    grep -q 'index out of range' bug.log || fail "expected a panic"
    ok "go test -tags bug: trailing-backslash corpus entry panics"
    if [ "$MODE" = fuzz ]; then
        "$GO" test -run '^$' -fuzz FuzzUnquote -fuzztime 10s ./escape \
            >fuzz.log 2>&1 || fail "fuzzing found: $(cat fuzz.log)"
        ok "go fuzz 10s: $(grep -o 'execs: [0-9]*' fuzz.log | tail -n 1)"
    fi
else
    echo "SKIP fuzz corpus card: '$GO' not found"
fi

# 6. HDL: simulation only, when Icarus Verilog is installed.
if command -v iverilog >/dev/null 2>&1 && command -v vvp >/dev/null 2>&1; then
    sh "$WORK/hdl-counter/verify.sh" >hdl.log 2>&1 || fail "hdl: $(cat hdl.log)"
    ok "hdl: counter and equivalent pass, wrapping fault rejected"
else
    echo "SKIP hdl card: iverilog/vvp not installed (simulation not run)"
fi

if [ "$MODE" = network ]; then
    command -v "$UV" >/dev/null 2>&1 || fail "network mode needs uv"
    cd "$WORK/behavior"
    "$UV" run -q --no-project --with "$HYPOTHESIS" python -m unittest \
        props_examples >props.log 2>&1 || fail "properties: $(cat props.log)"
    ok "hypothesis: properties and Cart state machine pass the reference"
    for variant in bug_split_drops_empty bug_cart_remove_noop; do
        if VARIANT=$variant "$UV" run -q --no-project --with "$HYPOTHESIS" \
            python -m unittest props_examples >"$variant.log" 2>&1; then
            fail "hypothesis missed $variant"
        fi
        ok "hypothesis rejects $variant"
    done
    grep -q "line=':'" bug_split_drops_empty.log || fail "split not shrunk"
    ok "hypothesis shrank the split counterexample to line=':'"

    cd "$WORK/package"
    PYTHONPATH=src "$PYTHON" -m unittest discover -s tests -p 'check_*.py' >checkout.log 2>&1 ||
        fail "checkout test"
    ok "package: test passes from the source checkout"
    install_and_test() {
        rm -rf "$WORK/dist" "$WORK/venv"
        "$UV" build -q --wheel -o "$WORK/dist" . &&
            "$UV" venv -q "$WORK/venv" &&
            "$UV" pip install -q --python "$WORK/venv/bin/python" \
                "$WORK"/dist/*.whl &&
            (cd "$WORK" && "$WORK/venv/bin/python" -m unittest discover \
                -s "$WORK/package/tests" -p 'check_*.py')
    }
    if install_and_test >wheel.log 2>&1; then
        fail "installed wheel passed without greetings.json"
    fi
    grep -q 'FileNotFoundError' wheel.log || fail "wrong wheel failure"
    ok "package: installed wheel fails with FileNotFoundError (data missing)"
    cp pyproject.fixed.toml pyproject.toml
    install_and_test >fixed.log 2>&1 || fail "fixed wheel: $(cat fixed.log)"
    ok "package: package-data fix makes the installed test pass"
fi

echo "$PASS checks passed"
