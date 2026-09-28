#!/usr/bin/env sh
# Installs the example instruction files under their real names in a
# throwaway demo project, checks them, and runs every listed command.
# The examples ship as *.example.md so that agents reading this skill do
# not load them as live instructions.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CHECK="$ROOT/../../scripts/check_instructions.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
cd "$WORK"
mkdir -p src/invoice tests web .claude/rules scripts
cp "$ROOT/AGENTS.example.md" AGENTS.md
cp "$ROOT/CLAUDE.example.md" CLAUDE.md
cp "$ROOT/rules-testing.example.md" .claude/rules/testing.md
cp "$ROOT/nested-AGENTS.example.md" web/AGENTS.md
cat >src/invoice/__init__.py <<'PY'
"""Invoice totals in integer cents."""


def total_cents(lines: list[tuple[int, int]]) -> int:
    return sum(price_cents * quantity for price_cents, quantity in lines)
PY
cat >tests/test_invoice.py <<'PY'
import sys
import unittest

sys.path.insert(0, "src")

from invoice import total_cents


class TotalTests(unittest.TestCase):
    def test_sums_price_times_quantity(self) -> None:
        self.assertEqual(total_cents([(250, 2), (99, 1)]), 599)


if __name__ == "__main__":
    unittest.main()
PY
touch tests/__init__.py
cat >scripts/generate_rates.py <<'PY'
"""Regenerate src/invoice/_rates_generated.py from a fixed table."""

from pathlib import Path

Path("src/invoice/_rates_generated.py").write_text("RATES = {'standard': 20}\n")
PY

"$PY" "$CHECK" AGENTS.md CLAUDE.md .claude/rules/testing.md web/AGENTS.md
echo 'PASS instruction files: no missing links or imports'

"$PY" "$CHECK" --commands AGENTS.md >commands.txt
count=0
while IFS= read -r command; do
    case $command in
        python3*)
            sh -c "$command" >/dev/null 2>&1 ||
                { echo "FAIL listed command failed: $command" >&2; exit 1; }
            count=$((count + 1))
            echo "PASS ran: $command"
            ;;
        *) echo "SKIP not run here: $command" ;;
    esac
done <commands.txt
[ "$count" -ge 2 ] || { echo 'FAIL expected two runnable commands' >&2; exit 1; }

cp "$ROOT/generic-AGENTS.example.txt" GENERIC.md
status=0
"$PY" "$CHECK" GENERIC.md >generic.log || status=$?
cat generic.log
[ "$status" -eq 1 ] || { echo 'FAIL generic file passed' >&2; exit 1; }
grep -q "generic phrase 'best practices'" generic.log
echo 'PASS generic instructions flagged'
echo 'VERIFY PASSED'
