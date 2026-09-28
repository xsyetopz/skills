#!/usr/bin/env sh
# Runs every semver.py command against the spec's examples, including
# check --from-tags in a throwaway Git repository.
#
#   sh verify.sh          run every check; exit 0 if all pass, 1 on the
#                         first failure
#   sh verify.sh --help   print this usage and exit 0
set -eu
case "${1:-}" in
    "") ;;
    -h | --help)
        cat <<'EOF'
usage: verify.sh

Runs every semver.py command (check, check --from-tags, compare, sort,
bump) against the SemVer 2.0.0 spec's examples. --from-tags runs in a
throwaway Git repository under mktemp -d.

Exit status:
  0  every check passed (the --from-tags check is skipped without git)
  1  a check failed
  2  unrecognized argument
EOF
        exit 0
        ;;
    *)
        echo 'usage: verify.sh [--help]' >&2
        exit 2
        ;;
esac
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SEMVER="$ROOT/../../scripts/semver.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM

fail() {
    echo "FAIL $1" >&2
    exit 1
}
# expect STATUS EXPECTED_STDOUT ARGS...: exact exit status and stdout.
expect() {
    want_status=$1 want_out=$2
    shift 2
    status=0
    out=$("$PY" -I "$SEMVER" "$@" 2>"$WORK/err") || status=$?
    [ "$status" -eq "$want_status" ] ||
        fail "semver.py $*: exit $status, expected $want_status: $(cat "$WORK/err")"
    [ "$out" = "$want_out" ] ||
        fail "semver.py $*: printed '$out', expected '$want_out'"
}

"$PY" -I "$SEMVER" --help | grep -q '^Exit status:' || fail '--help'
echo 'PASS --help documents exit status'

out=$("$PY" -I "$SEMVER" check 1.0.0-alpha+001 1.0.0-0A 1.0.0-x-y-z.-- \
    1.0.0+21AF26D3----117B344092BD) || fail "check rejected a valid version: $out"
echo "$out" | grep -q '^PASS  1.0.0-alpha+001$' || fail 'check prints PASS'
echo "$out" | grep -q '^4/4 valid$' || fail "check count: $out"
echo 'PASS check accepts leading zeros in build metadata and hyphens'

for bad in 1.2 01.2.3 v1.2.3 1.2.3-01 1.2.3-alpha..1 1.2.3+ 1.2.3-a_b; do
    status=0
    "$PY" -I "$SEMVER" check "$bad" >"$WORK/out" || status=$?
    [ "$status" -eq 1 ] || fail "check $bad: exit $status, expected 1"
    grep -q "^FAIL  $bad  - " "$WORK/out" || fail "check $bad: no reason"
done
echo 'PASS check rejects each grammar violation with a reason'

"$PY" -I "$SEMVER" check --json 2.0.0-rc.1+sha.5114f85 >"$WORK/json"
"$PY" -I -c 'import json, sys
r = json.load(open(sys.argv[1]))[0]
assert r["prerelease"] == ["rc", "1"] and r["build"] == ["sha", "5114f85"], r
' "$WORK/json" || fail 'check --json fields'
echo 'PASS check --json splits pre-release and build identifiers'

if command -v git >/dev/null 2>&1; then
    export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/gitconfig"
    export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
    export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
    git init -q "$WORK/repo"
    git -C "$WORK/repo" commit -q --allow-empty -m init
    git -C "$WORK/repo" tag v1.0.0
    git -C "$WORK/repo" tag 1.1.0-rc.1
    out=$(cd "$WORK/repo" && "$PY" -I "$SEMVER" check --from-tags)
    echo "$out" | grep -q "^PASS  v1.0.0  (leading 'v' is a tag prefix" ||
        fail "--from-tags did not note the v prefix: $out"
    echo "$out" | grep -q '^2/2 valid$' || fail "--from-tags count: $out"
    git -C "$WORK/repo" tag release-2
    status=0
    (cd "$WORK/repo" && "$PY" -I "$SEMVER" check --from-tags >/dev/null) ||
        status=$?
    [ "$status" -eq 1 ] || fail "--from-tags accepted release-2"
    echo 'PASS check --from-tags notes v prefixes and rejects other tags'
else
    echo 'SKIP check --from-tags: git not found'
fi

# Spec item 11: each adjacent pair of the canonical chain is ascending.
set -- 1.0.0-alpha 1.0.0-alpha.1 1.0.0-alpha.beta 1.0.0-beta 1.0.0-beta.2 \
    1.0.0-beta.11 1.0.0-rc.1 1.0.0
prev=
for v in "$@"; do
    [ -z "$prev" ] || expect 0 '<' compare "$prev" "$v"
    prev=$v
done
expect 0 '=' compare 1.0.0+a 1.0.0+b
expect 0 '>' compare 1.10.0 1.9.0
expect 1 '' compare 1.0 1.0.0
echo 'PASS compare follows the spec precedence chain and ignores build'

want=$(printf '%s\n' "$@")
expect 0 "$want" sort 1.0.0 1.0.0-rc.1 1.0.0-beta.11 1.0.0-beta.2 \
    1.0.0-beta 1.0.0-alpha.beta 1.0.0-alpha.1 1.0.0-alpha
expect 0 "$(printf '1.0.0+b\n1.0.0+a')" sort 1.0.0+b 1.0.0+a
echo 'PASS sort orders by precedence, stable for build-only differences'

expect 0 2.0.0 bump 1.4.7+sha.1 major
expect 0 1.5.0 bump 1.4.7 minor
expect 0 1.4.8 bump 1.4.7 patch
expect 0 2.0.0-rc.1 bump 1.4.7 major --pre-id rc
expect 0 1.4.8-alpha.1 bump 1.4.7 prerelease --pre-id alpha
expect 0 2.0.0-rc.2 bump 2.0.0-rc.1 prerelease
expect 0 2.0.0-rc.1 bump 2.0.0-beta.3 prerelease --pre-id rc
expect 1 '' bump 2.0.0-rc.1 prerelease --pre-id alpha
expect 0 2.0.0+sha.0a1b2c3 bump 2.0.0-rc.3 release --build sha.0a1b2c3
expect 1 '' bump 2.0.0 release
expect 2 '' bump 1.4.7 prerelease
expect 2 '' bump 1.4.7 patch --build a_b
echo 'PASS bump applies resets, pre-release trains, release, and build'
echo 'VERIFY PASSED'
