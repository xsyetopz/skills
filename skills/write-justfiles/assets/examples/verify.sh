#!/usr/bin/env sh
# Runs every construct in the example justfiles in a disposable copy and
# compares exact output and exit status. Requires just >= 1.55.
#
#   sh verify.sh          all checks
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
command -v just >/dev/null 2>&1 || {
    echo 'SKIP: just not found'
    exit 0
}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/." "$WORK/"
cd "$WORK"
PASSED=0

fail() {
    printf 'FAIL %s\n%s\n' "$1" "$2" >&2
    exit 1
}

# expect LABEL EXPECTED_STATUS EXPECTED_STDOUT -- COMMAND...
expect() {
    label=$1
    want_status=$2
    want_out=$3
    shift 4
    status=0
    out=$("$@" 2>"$WORK/stderr") || status=$?
    [ "$status" -eq "$want_status" ] ||
        fail "$label" "exit $status, expected $want_status: $(cat "$WORK/stderr")"
    [ "$out" = "$want_out" ] ||
        fail "$label" "stdout was:
$out
expected:
$want_out"
    PASSED=$((PASSED + 1))
    echo "PASS $label"
}

nl='
'
just --fmt --check >/dev/null
for f in tools eager lazy dotenv require; do
    just --fmt --check --justfile "$f.just" >/dev/null
done
echo 'PASS fmt --check on every example'

expect split-interpolation 0 "[a]${nl}[b]" -- \
    just split-interpolation 'a b'
expect quote-function 0 "[a b]${nl}[it's]" -- \
    sh -c "just quoted 'a b' && just quoted \"it's\""
# shellcheck disable=SC2016 # '$HOME' must reach the recipe unexpanded
expect positional-arguments 0 "[a b]${nl}[\$HOME]${nl}[]" -- \
    just positional 'a b' '$HOME' ''
expect exported-parameter 0 "[a \"b\" c]" -- just exported 'a "b" c'
expect default-parameter 0 'hello world' -- just greet
expect default-overridden 0 'hello team' -- just greet team
expect variadic-plus 0 "[x]${nl}[y z]" -- just at-least-one x 'y z'
expect variadic-plus-empty 1 '' -- just at-least-one
expect arg-long 0 'level=debug' -- just log --level debug
expect arg-pattern-reject 1 '' -- just log --level loud
expect prior-dependency 0 "prepare${nl}build" -- just build
expect subsequent-dependency 0 "prepare${nl}build${nl}release${nl}announce" \
    -- just release
expect dependency-arguments 0 "deploy staging${nl}deploy production" -- \
    just deploy-all
out=$(just parallel-pair | sort)
[ "$out" = "a saw b${nl}b saw a" ] || fail parallel "$out"
echo 'PASS parallel-dependencies'
PASSED=$((PASSED + 1))
expect line-shells 0 "$WORK" -- just line-shells
expect script-recipe 0 '/' -- just one-script
expect fail-fast 3 '' -- just fail-fast
expect masked-failure 0 'still reported success' -- just masked-failure
expect confirm-without-yes 1 '' -- sh -c 'just clean </dev/null'
expect confirm-with-yes 0 'removed /tmp/example-cache' -- just --yes clean
expect os-attribute 0 'unix' -- just platform
expect working-directory 0 'sub' -- just in-sub
expect no-cd 0 "$WORK/sub" -- sh -c "cd sub && just from-caller"
expect env-attribute 0 'hi' -- just with-env
expect env-default 0 '/tmp/example-cache' -- just show-cache
expect env-override 0 '/tmp/other' -- env CACHE_DIR=/tmp/other just show-cache
expect cli-override 0 '/tmp/cli' -- just cache_dir=/tmp/cli show-cache
# os() uses Rust's std::env::consts::OS names: macos, linux, windows, ...
case $(uname) in
    Darwin) os=macos ;;
    Linux) os=linux ;;
    *) os=unknown ;;
esac
expect conditional-local 0 "mode=local os=$os" -- env -u CI just show-mode
expect conditional-ci 0 "mode=ci os=$os" -- env CI=1 just show-mode
expect module 0 'tools 1.0' -- just tools::version
expect eager-backtick 0 'unrelated' -- just --justfile eager.just unrelated
[ -e eager.marker ] || fail eager-backtick 'backtick did not run'
expect lazy-backtick 0 'unrelated' -- just --justfile lazy.just unrelated
[ ! -e lazy.marker ] || fail lazy-backtick 'backtick ran despite set lazy'
expect dotenv 0 'token=from-dotenv' -- just --justfile dotenv.just show-token
mv example.env example.env.off
expect dotenv-required 1 '' -- just --justfile dotenv.just show-token
mv example.env.off example.env
expect require-missing 1 '' -- just --justfile require.just use-tool
grep -q 'definitely-not-installed-tool' "$WORK/stderr" ||
    fail require-missing 'error does not name the tool'
expect dry-run 0 '' -- just --dry-run fail-fast
expect evaluate 0 '/tmp/example-cache' -- just --evaluate cache_dir
summary=$(just --summary)
case " $summary " in
    *" build "*" tools::version "*) ;;
    *) fail summary "$summary" ;;
esac
echo 'PASS summary'
PASSED=$((PASSED + 1))
just --dump --dump-format json |
    python3 -c 'import json,sys; d=json.load(sys.stdin); assert "build" in d["recipes"]'
echo 'PASS dump-json'
PASSED=$((PASSED + 1))
echo "VERIFY PASSED: $PASSED checks"
