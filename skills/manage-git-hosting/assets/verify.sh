#!/usr/bin/env sh
# Checks the bundled tools and the read-only commands from the cards.
#
#   sh verify.sh           offline: tools against a fake gh that records
#                          every call (no request leaves the machine)
#   sh verify.sh network   also READ-ONLY calls to public repositories
#                          (cli/cli on GitHub, gitlab-org/gitlab on
#                          GitLab). Nothing is created or changed.
set -eu
SKILL=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | network) ;;
    *)
        echo 'usage: verify.sh [verify|network]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

"$PYTHON" "$SKILL/scripts/test_hosting_tools.py" >"$WORK/t.log" 2>&1 ||
    fail "tool tests: $(tail -n 20 "$WORK/t.log")"
ok "sync_labels and upsert_comment: $(grep -E '^Ran ' "$WORK/t.log") (fake gh)"

if [ "$MODE" = network ]; then
    command -v gh >/dev/null 2>&1 || fail "network mode needs gh"
    repo=cli/cli
    view=$(gh repo view "$repo" --json nameWithOwner,defaultBranchRef,viewerPermission \
        --jq '"\(.nameWithOwner) default=\(.defaultBranchRef.name) viewer=\(.viewerPermission)"')
    ok "resolve target: $view"
    pr=$(gh pr list -R "$repo" --state merged --limit 1 --json number --jq '.[0].number')
    head=$(gh pr view "$pr" -R "$repo" --json headRefOid,state \
        --jq '"\(.state) head=\(.headRefOid[0:12])"')
    ok "read PR #$pr before acting: $head"
    rel=$(gh release view -R "$repo" --json tagName,isDraft,assets \
        --jq '"\(.tagName) draft=\(.isDraft) assets=\(.assets|length)"')
    ok "read latest release: $rel"
    printf '[{"name":"bug","color":"000000","description":"x"}]\n' >"$WORK/labels.json"
    "$PYTHON" "$SKILL/scripts/sync_labels.py" "$repo" "$WORK/labels.json" \
        >"$WORK/plan.log" || fail "label plan"
    grep -q '^plan gh label edit bug' "$WORK/plan.log" ||
        fail "unexpected plan: $(cat "$WORK/plan.log")"
    ok "sync_labels dry run against $repo: $(head -n 1 "$WORK/plan.log" | cut -c1-60)"
    printf 'report\n' >"$WORK/body.md"
    "$PYTHON" "$SKILL/scripts/upsert_comment.py" "$repo" "$pr" verify-probe \
        "$WORK/body.md" >"$WORK/upsert.log" || fail "upsert dry run"
    grep -q "^plan create comment on #$pr" "$WORK/upsert.log" ||
        fail "unexpected: $(cat "$WORK/upsert.log")"
    ok "upsert_comment dry run: $(cat "$WORK/upsert.log")"
    remaining=$(gh api rate_limit --jq '.resources.core.remaining')
    ok "rate limit readable: core remaining=$remaining"
    gl=$(curl -fsS 'https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab' |
        "$PYTHON" -c 'import json,sys; d=json.load(sys.stdin); print(d["path_with_namespace"], "default=" + d["default_branch"])') ||
        fail "gitlab read"
    ok "gitlab project read: $gl"
fi

echo "$PASS checks passed"
