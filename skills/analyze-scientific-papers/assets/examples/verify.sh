#!/usr/bin/env sh
# Checks the bundled research tools.
#
#   sh verify.sh           offline: helper tests, statcheck-style checks on
#                          the example results, evidence-note rules
#   sh verify.sh network   also live, read-only metadata queries (arXiv,
#                          Crossref, OpenAlex), a Crossref retraction lookup,
#                          and a SciPy 1.16.2 cross-check (via uv)
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
S="$ROOT/../../scripts"
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

for test in test_analysis_tools test_fetch_metadata; do
    "$PYTHON" "$S/$test.py" >"$WORK/$test.log" 2>&1 ||
        fail "$test: $(tail -n 20 "$WORK/$test.log")"
    ok "$test: $(grep -E '^Ran ' "$WORK/$test.log")"
done

if "$PYTHON" "$S/check_stats.py" "$ROOT/results-section.txt" >"$WORK/s.log"; then
    fail "inconsistent report not flagged"
fi
grep -q "FLAG 't(28) = 1.20, p = .03'" "$WORK/s.log" || fail "wrong flag"
ok "check_stats: $(tail -n 1 "$WORK/s.log"); flags t(28) = 1.20, p = .03"

"$PYTHON" "$S/check_evidence_note.py" "$ROOT/note-supported.md" >/dev/null ||
    fail "supported note rejected"
if "$PYTHON" "$S/check_evidence_note.py" "$ROOT/note-abstract-only.md" >"$WORK/n.log"; then
    fail "abstract-only support accepted"
fi
ok "evidence notes: full-text note passes; abstract-only 'supported' rejected"

if [ "$MODE" = network ]; then
    "$PYTHON" "$S/fetch_metadata.py" --provider arxiv --query 'all:"tail sampling"' \
        --limit 3 >"$WORK/arxiv.xml" || fail "arxiv fetch"
    ok "arxiv: $(grep -c '<entry>' "$WORK/arxiv.xml") entries (live Atom)"
    sleep 3 # arXiv asks for at least 3 s between requests
    "$PYTHON" "$S/fetch_metadata.py" --provider openalex \
        --query 'distributed tracing tail sampling' --limit 3 >"$WORK/oa.json" ||
        fail "openalex fetch"
    ok "openalex: $("$PYTHON" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["results"]), "results")' "$WORK/oa.json")"
    "$PYTHON" "$S/fetch_metadata.py" --provider crossref --query retraction \
        --param 'filter=updates:10.1016/S0140-6736(97)11096-0' --limit 5 \
        >"$WORK/cr.json" || fail "crossref fetch"
    types=$("$PYTHON" -c 'import json,sys; d=json.load(open(sys.argv[1]))["message"]["items"]; print(sorted(u["type"] for i in d for u in i.get("update-to", [])))' "$WORK/cr.json")
    case "$types" in
        *retraction*) ok "crossref updates lookup: $types" ;;
        *) fail "retraction not found: $types" ;;
    esac
    uv run -q --no-project --with scipy==1.16.2 python - "$S" >"$WORK/scipy.log" <<'EOF' ||
import itertools
import sys

sys.path.insert(0, sys.argv[1])
import check_stats as c
from scipy import stats

worst = 0.0
for stat, df in itertools.product([0.3, 1.2, 2.2, 3.7, 8.5], [1, 3, 12, 57, 400]):
    worst = max(worst, abs(c.p_value("t", stat, df, None) - 2 * stats.t.sf(stat, df)))
    worst = max(worst, abs(c.p_value("chi2", stat, df, None) - stats.chi2.sf(stat, df)))
    for df2 in (5, 30, 200):
        worst = max(worst, abs(c.p_value("F", stat, df, df2) - stats.f.sf(stat, df, df2)))
print(f"{worst:.1e}")
assert worst < 1e-9, worst
EOF
        fail "scipy cross-check: $(cat "$WORK/scipy.log")"
    ok "check_stats vs scipy 1.16.2: max abs difference $(cat "$WORK/scipy.log")"
fi

echo "$PASS checks passed"
