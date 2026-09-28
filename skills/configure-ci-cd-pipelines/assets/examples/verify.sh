#!/usr/bin/env sh
# Runs every pipeline check from the references in a disposable copy.
#
#   sh verify.sh           offline: actionlint, pin check, aggregator
#                          truth table, runner shell semantics
#   sh verify.sh network   also zizmor 1.30.1 and check-jsonschema 0.38.2
#                          (via uvx), and resolves pinned SHAs with gh
#
# No pipeline runs on a hosted provider here; hosted behavior (secrets,
# approvals, required checks) is listed per card as not run.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
PINS="$ROOT/../../scripts/check_action_pins.py"
MODE=${1:-verify}
case "$MODE" in
    verify | network) ;;
    *)
        echo 'usage: verify.sh [verify|network]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
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

# 1. actionlint: good workflow clean, bad one reports the injection.
if command -v actionlint >/dev/null 2>&1; then
    actionlint -no-color github/good/.github/workflows/ci.yml >lint.log 2>&1 ||
        fail "actionlint good: $(cat lint.log)"
    ok "actionlint $(actionlint --version | head -n 1): good workflow clean"
    if actionlint -no-color github/bad/.github/workflows/ci.yml >bad.log 2>&1; then
        fail "actionlint accepted the bad workflow"
    fi
    grep -q 'potentially untrusted' bad.log || fail "no injection finding"
    ok "actionlint: bad workflow, title expression in run: is untrusted"
else
    echo "SKIP actionlint cards: actionlint not installed"
fi

# 2. Pins: tags are reported, SHAs pass.
status=0
"$PYTHON" "$PINS" github/bad >pins.log || status=$?
[ "$status" -eq 1 ] || fail "pin check exit $status on bad"
grep -q '^2 finding' pins.log || fail "expected 2 unpinned uses"
"$PYTHON" "$PINS" github/good >/dev/null || fail "good workflow has unpinned uses"
ok "check_action_pins: bad has 2 tag pins, good has 0"

# 3. Required-check aggregator truth table.
agg=github/good/ci/all-green.sh
while read -r event test title want; do
    status=0
    bash "$agg" "$event" "$test" "$title" >/dev/null || status=$?
    [ "$status" -eq "$want" ] ||
        fail "all-green $event $test $title: exit $status, want $want"
done <<'EOF'
pull_request success success 0
push success skipped 0
pull_request success skipped 1
push failure skipped 1
pull_request cancelled success 1
push success success 1
EOF
ok "all-green.sh: 6 result combinations give the expected exit codes"

# 4. Runner shell invocations from the workflow syntax docs.
printf 'false | tee /dev/null\necho reached\n' >pipe.sh
bash --noprofile --norc -eo pipefail pipe.sh >explicit.log 2>&1 && explicit=0 ||
    explicit=$?
bash -e pipe.sh >unspecified.log 2>&1 && unspecified=0 || unspecified=$?
sh -e pipe.sh >sh.log 2>&1 && shell_sh=0 || shell_sh=$?
[ "$explicit" -eq 1 ] && [ "$unspecified" -eq 0 ] && [ "$shell_sh" -eq 0 ] ||
    fail "shell exits: bash=$explicit unspecified=$unspecified sh=$shell_sh"
ok "failing pipe: shell: bash exits 1; unspecified (bash -e) and sh -e exit 0"

if command -v shellcheck >/dev/null 2>&1; then
    shellcheck github/good/ci/*.sh || fail "shellcheck ci scripts"
    ok "shellcheck: ci scripts clean"
fi

if [ "$MODE" = network ]; then
    command -v uvx >/dev/null 2>&1 || fail "network mode needs uvx"
    uvx zizmor@1.30.1 --offline --no-progress github/good >zg.log 2>&1 ||
        fail "zizmor good: $(cat zg.log)"
    ok "zizmor: good workflow, no findings"
    uvx zizmor@1.30.1 --offline --no-progress github/bad >zb.log 2>&1 || true
    for rule in dangerous-triggers template-injection unpinned-uses \
        excessive-permissions artipacked; do
        grep -q "\[$rule\]" zb.log || fail "zizmor missed $rule"
    done
    ok "zizmor: bad workflow, 5 rule kinds reported"
    cjs="uvx check-jsonschema@0.38.2"
    $cjs --builtin-schema vendor.gitlab-ci gitlab/.gitlab-ci.yml >/dev/null ||
        fail "gitlab schema"
    if $cjs --builtin-schema vendor.gitlab-ci gitlab/broken.gitlab-ci.yml \
        >gb.log 2>&1; then
        fail "gitlab schema accepted the broken file"
    fi
    ok "gitlab: valid file passes, broken needs entry rejected"
    $cjs --builtin-schema vendor.bitbucket-pipelines \
        bitbucket/bitbucket-pipelines.yml >/dev/null || fail "bitbucket schema"
    if $cjs --builtin-schema vendor.bitbucket-pipelines \
        bitbucket/broken.bitbucket-pipelines.yml >bb.log 2>&1; then
        fail "bitbucket schema accepted max-time: thirty"
    fi
    printf 'pipelines:\n  default:\n    - step:\n        scripts: [x]\n' >typo.yml
    $cjs --builtin-schema vendor.bitbucket-pipelines typo.yml >/dev/null ||
        fail "schema behavior changed: typo now rejected"
    ok "bitbucket: type error rejected; 'scripts' key typo passes the schema"
    if command -v gh >/dev/null 2>&1; then
        "$PYTHON" "$PINS" --resolve github/good >resolve.log ||
            fail "pins do not match tags: $(cat resolve.log)"
        ok "pinned SHAs match their # vX.Y.Z tags (gh api)"
    fi
fi

echo "$PASS checks passed"
