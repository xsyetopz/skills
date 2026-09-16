#!/usr/bin/env sh
# Run in a disposable copy. No installation, lock regeneration, or source cleanup.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
cp -R "$ROOT/." "$WORK/"
cd "$WORK"
MODE=${1:-all}
CASE=${2:-}
if [ "$#" -gt 2 ] || { [ -n "$CASE" ] && [ "$MODE" != correctness ]; }; then
    echo 'usage: verify.sh [all|comparisons|correctness [1..8]|reproduction|benchmark]' >&2; exit 2
fi
if [ -n "$CASE" ]; then case "$CASE" in 1|2|3|4|5|6|7|8) ;; *) echo 'case must be 1..8' >&2; exit 2;; esac; fi
case "$MODE" in all|comparisons|correctness|reproduction|benchmark) ;; *)
    echo 'usage: verify.sh [all|comparisons|correctness|reproduction|benchmark]' >&2; exit 2;; esac
pair() {
    topic=$1; shift
    status=0
    output=$("$@" red "$topic" 2>&1) || status=$?
    if [ "$status" -ne 1 ]; then printf '%s\n' "$output"; echo "mutant did not fail its contract (exit $status)" >&2; exit 1; fi
    case "$output" in *"CONTRACT topic $topic: FAIL"*) ;; *) printf '%s\n' "$output"; echo 'wrong failure; not an oracle result' >&2;exit 1;; esac
    printf '%s\n' "$output"
    output=$("$@" green "$topic")
    case "$output" in *"CONTRACT topic $topic: PASS"*) ;; *) echo 'correction did not satisfy its contract' >&2;exit 1;; esac
    printf '%s\n' "$output"
}
JAVA=${JAVA:-java}; KOTLINC=${KOTLINC:-kotlinc}
"$KOTLINC" -version
"$KOTLINC" comparisons/Pairs.kt correctness/Semantics.kt reproduction/Repro.kt -Werror -include-runtime -d examples.jar
correctness() { for n in ${CASE:-1 2 3 4 5 6 7 8}; do pair "$n" "$JAVA" -cp examples.jar SemanticsKt; done; }
comparisons() { "$JAVA" -cp examples.jar Pairs verify; }
reproduction() { "$JAVA" -cp examples.jar ReproKt; }
case "$MODE" in
    all) comparisons; correctness; reproduction;;
    benchmark)
        echo 'Legacy benchmark mode: execution smoke only; no timing measurements.'
        comparisons
        echo 'SMOKE PASSED: baseline/candidate result checks; not a performance result.'
        ;;
    comparisons) comparisons;;
    correctness) correctness;;
    reproduction) reproduction;;
esac
