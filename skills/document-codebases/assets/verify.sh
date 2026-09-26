#!/usr/bin/env sh
# Checks the documentation tools on the example project in a temp copy.
#
#   sh verify.sh
#
# Runs the documented commands of the example README (correct and broken
# versions), checks links and anchors, checks a formatting-only rewrite
# with same_words.py, and lints the example with the bundled
# markdownlint config through bunx (skipped without bun).
set -eu
SKILL=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$SKILL/assets/examples/wordfreq" "$WORK/wordfreq"
S="$SKILL/scripts"
E="$WORK/wordfreq"
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

"$PYTHON" "$S/test_doc_tools.py" >"$WORK/t.log" 2>&1 || fail "$(tail -n 20 "$WORK/t.log")"
ok "doc tools: $(grep -E '^Ran ' "$WORK/t.log")"

"$PYTHON" "$S/check_doc_commands.py" "$E/README.md" >"$WORK/c.log" ||
    fail "README commands: $(cat "$WORK/c.log")"
ok "README commands: $(tail -n 1 "$WORK/c.log")"
if "$PYTHON" "$S/check_doc_commands.py" "$E/README.broken.txt" >"$WORK/b.log"; then
    fail "broken README passed"
fi
grep -q 'unrecognized arguments: --limit' "$WORK/b.log" || fail "wrong failure"
ok "broken README: documented --limit flag fails with argparse's error"
"$PYTHON" "$S/check_doc_commands.py" "$E/CONTRIBUTING.md" >/dev/null ||
    fail "CONTRIBUTING commands"
ok "CONTRIBUTING commands pass"

"$PYTHON" "$S/check_links.py" "$E/README.md" "$E/CONTRIBUTING.md" >"$WORK/l.log" ||
    fail "links: $(cat "$WORK/l.log")"
ok "links: $(tail -n 1 "$WORK/l.log")"
if "$PYTHON" "$S/check_links.py" "$E/README.broken.txt" >"$WORK/lb.log"; then
    fail "broken links passed"
fi
ok "broken links: $(grep -c '^error' "$WORK/lb.log") errors (anchor #flags, missing file)"

"$PYTHON" - "$E/CONTRIBUTING.md" "$WORK/reflowed.md" <<'EOF'
import sys
text = open(sys.argv[1]).read()
reflowed = text.replace("before opening a pull request:", "before\nopening a pull request:")
open(sys.argv[2], "w").write(reflowed)
EOF
"$PYTHON" "$S/same_words.py" "$E/CONTRIBUTING.md" "$WORK/reflowed.md" >/dev/null ||
    fail "rewrap reported as a change"
sed 's/unittest discover/unittest discover -v/' "$E/CONTRIBUTING.md" >"$WORK/changed.md"
if "$PYTHON" "$S/same_words.py" "$E/CONTRIBUTING.md" "$WORK/changed.md" >/dev/null; then
    fail "changed command not detected"
fi
ok "same_words: rewrap passes, a changed command in a code block fails"

if command -v bunx >/dev/null 2>&1; then
    cp "$SKILL/assets/.markdownlint-cli2.jsonc" "$E/"
    (cd "$E" && bunx markdownlint-cli2 README.md CONTRIBUTING.md >"$WORK/md.log" 2>&1) ||
        fail "markdownlint: $(cat "$WORK/md.log")"
    ok "markdownlint with the bundled config: README and CONTRIBUTING clean"
else
    echo "SKIP markdownlint: bunx not found"
fi

echo "$PASS checks passed"
