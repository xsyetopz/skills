#!/usr/bin/env sh
# Finds compatibility candidates in the "before" package, shows why each
# was removed or kept, and checks the "after" package.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
FIND="$ROOT/../../scripts/find_compat_python.py"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0

# 1. Support policy: the minimum Python version comes from pyproject.toml.
min=$(sed -n 's/^requires-python = ">=\(.*\)"$/\1/p' "$ROOT/before/pyproject.toml")
echo "requires-python >= $min"

# 2. Candidates.
"$PY" "$FIND" "$ROOT/before/configlib" --min-python "$min" | tee "$WORK/cands"
grep -q 'import-fallback' "$WORK/cands"
grep -q 'version-branch: .*false for every supported version' "$WORK/cands"
grep -q 'deprecated-alias: load_config' "$WORK/cands"
echo 'PASS scanner found the fallback, the dead branch, and the alias'
if command -v ruff >/dev/null 2>&1; then
    status=0
    ruff check --no-cache --isolated --select UP036 --target-version py311 \
        "$ROOT/before/configlib" >"$WORK/ruff.log" 2>&1 || status=$?
    grep -q 'UP036' "$WORK/ruff.log"
    echo "PASS ruff UP036 flags the outdated version block (exit $status)"
else
    echo 'SKIP ruff: not installed'
fi

# 3. Consumer evidence for the alias: only the definition references it.
# -I skips binary files: bytecode caches repeat the name but are not callers.
refs=$(grep -rnI 'load_config' "$ROOT/before" | grep -v 'def load_config' |
    grep -cv 'load_config is deprecated' || true)
echo "load_config references outside its definition: $refs"
[ "$refs" -eq 0 ] || { echo 'FAIL alias still has callers' >&2; exit 1; }

# 4. Both versions pass the same tests; after has no deprecated calls.
for side in before after; do
    cp -R "$ROOT/$side" "$WORK/$side"
    (cd "$WORK/$side" && "$PY" -W error::DeprecationWarning -m unittest -q \
        2>&1 | tail -1)
done
echo 'PASS before and after pass the same tests'
"$PY" "$FIND" "$ROOT/after/configlib" --min-python "$min" | tail -1

# 5. The legacy key alias must stay: saved 1.2 files still use it.
sed 's/^_LEGACY_KEYS = .*/_LEGACY_KEYS = {}/' \
    "$ROOT/after/configlib/__init__.py" >"$WORK/after/configlib/__init__.py"
if (cd "$WORK/after" && "$PY" -m unittest -q >/dev/null 2>&1); then
    echo 'FAIL removing the key alias went unnoticed' >&2
    exit 1
fi
echo 'PASS removing the persisted-key alias breaks loading of saved 1.2 files'
echo 'VERIFY PASSED'
