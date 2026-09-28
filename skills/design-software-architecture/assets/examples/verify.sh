#!/usr/bin/env sh
# Runs the architecture example and the layer checker in a temp copy.
#
#   sh verify.sh
#
# The orders example: port contract tests on the memory and SQLite
# adapters, idempotent retries, and an HTTP adapter with RFC 9457
# problem responses. The layer rules pass, and a planted domain ->
# adapter import is rejected.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
S="$ROOT/../../scripts"
PYTHON=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/orders" "$WORK/orders"
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

"$PYTHON" "$S/test_check_layers.py" >"$WORK/t.log" 2>&1 || fail "$(tail -n 20 "$WORK/t.log")"
ok "check_layers tests: $(grep -E '^Ran ' "$WORK/t.log")"

"$PYTHON" -W error "$WORK/orders/tests/test_orders.py" >"$WORK/o.log" 2>&1 ||
    fail "orders: $(tail -n 20 "$WORK/o.log")"
ok "orders: $(grep -E '^Ran ' "$WORK/o.log") (contract x2 adapters, idempotency, HTTP)"

"$PYTHON" "$S/check_layers.py" "$WORK/orders/layers.json" >"$WORK/l.log" ||
    fail "layers: $(cat "$WORK/l.log")"
ok "layers: $(tail -n 1 "$WORK/l.log")"

printf '\nfrom orders.adapters.sqlite import SqliteStore\n' >>"$WORK/orders/orders/domain.py"
if "$PYTHON" "$S/check_layers.py" "$WORK/orders/layers.json" >"$WORK/m.log"; then
    fail "planted domain -> adapter import passed"
fi
grep -q 'domain imports adapters' "$WORK/m.log" || fail "wrong violation"
grep -q 'import cycle' "$WORK/m.log" || fail "cycle not reported"
ok "planted domain -> adapters import: direction violation and cycle reported"

"$PYTHON" "$ROOT/protocols/test_lsp_framing.py" >"$WORK/p.log" 2>&1 ||
    fail "lsp framing: $(tail -n 20 "$WORK/p.log")"
ok "lsp framing: $(grep -E '^Ran ' "$WORK/p.log") (byte lengths, split reads, UTF-16)"

echo "$PASS checks passed"
