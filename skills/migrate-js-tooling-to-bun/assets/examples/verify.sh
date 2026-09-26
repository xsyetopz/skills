#!/usr/bin/env sh
# Runs every migration check from the references against the bundled
# fixtures in a disposable copy. Offline: the fixtures have no registry
# dependencies. BUN, NODE, and PYTHON override the executables.
#
#   sh verify.sh
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
COMPARE="$ROOT/../../scripts/compare_lockfiles.py"
BUN=${BUN:-bun}
NODE=${NODE:-node}
PYTHON=${PYTHON:-python3}
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

for tool in "$BUN" "$NODE" "$PYTHON"; do
    command -v "$tool" >/dev/null 2>&1 || fail "missing executable: $tool"
done
echo "bun $("$BUN" --version) ($("$BUN" --revision)), node $("$NODE" --version)"

# 1. Automatic lockfile migration keeps package-lock.json and the graph.
cp -R "$ROOT/npm-project" "$WORK/npm"
cd "$WORK/npm"
"$BUN" install >install.log 2>&1 || fail "bun install on npm project"
[ -f bun.lock ] || fail "bun.lock not written"
[ -f package-lock.json ] || fail "package-lock.json removed"
grep -q '"configVersion": 0' bun.lock || fail "npm migration configVersion"
ok "package-lock.json migrated to bun.lock; original kept"
"$PYTHON" "$COMPARE" package-lock.json bun.lock >compare.log ||
    fail "resolutions changed: $(cat compare.log)"
ok "compare_lockfiles: $(head -n 1 compare.log)"
[ -d node_modules/@fixture/util ] || fail "hoisted layout expected"
ok "migrated npm workspace installs hoisted (configVersion 0)"

# 2. Lifecycle scripts of a file: dependency are blocked until trusted.
[ ! -f node_modules/native-dep/built.txt ] || fail "postinstall ran untrusted"
grep -q 'Blocked 1 postinstall' install.log || fail "no blocked-script notice"
"$BUN" pm untrusted 2>&1 | grep -q 'native-dep' || fail "pm untrusted list"
ok "file: dependency postinstall blocked; bun pm untrusted lists it"
"$BUN" pm trust native-dep >/dev/null 2>&1 || fail "bun pm trust"
[ -f node_modules/native-dep/built.txt ] || fail "trusted postinstall did not run"
grep -q '"trustedDependencies"' package.json || fail "trust not recorded"
ok "bun pm trust ran the script and wrote trustedDependencies"

# 3. Frozen installs: manifest drift fails; a new workspace edge does not.
"$BUN" ci >/dev/null 2>&1 || fail "bun ci on unchanged project"
ok "bun ci passes on the committed lockfile"
cp package.json package.json.orig
sed 's#"file:./native-dep"#"file:./native-dep", "extra": "file:./native-dep"#' \
    package.json.orig >package.json
if "$BUN" ci >ci.log 2>&1; then
    fail "bun ci accepted a new dependency"
fi
grep -q 'lockfile had changes, but lockfile is frozen' ci.log ||
    fail "unexpected bun ci error: $(cat ci.log)"
ok "bun ci rejects an added dependency (exit 1, lockfile is frozen)"
cp package.json.orig package.json
cp bun.lock bun.lock.orig
util=packages/util/package.json
cp "$util" util.orig
sed 's#"type": "module"#"type": "module", "dependencies": {"@fixture/app": "workspace:*"}#' \
    util.orig >"$util"
"$BUN" ci >/dev/null 2>&1 || fail "bun ci behavior changed for workspace edge"
cmp -s bun.lock bun.lock.orig || fail "bun ci wrote the lockfile"
ok "gap: bun ci accepts a new workspace:* edge and leaves bun.lock as is"
"$BUN" install --lockfile-only >/dev/null 2>&1 || fail "lockfile-only"
if cmp -s bun.lock bun.lock.orig; then
    fail "lockfile-only did not record the workspace edge"
fi
ok "bun install --lockfile-only + diff exposes the workspace edge"
cp util.orig "$util"
cp bun.lock.orig bun.lock

# 4. The package manager migration does not change the script runtime.
"$BUN" run start 2>/dev/null | grep -q '(node ' || fail "bun run start runtime"
ok "bun run start keeps the script's node executable"
"$BUN" --bun run start 2>/dev/null | grep -q '(bun ' || fail "--bun runtime"
ok "bun --bun run start runs the same script on Bun"

# 5. Test runner: bun:test mocks, globals, preload, coverage, mutation.
cat >packages/util/globals.test.js <<'EOF'
import { slug } from "./index.js";

test("globals need no import", () => {
  expect(slug("A B")).toBe("a-b");
  expect(globalThis.__preloaded).toBe(true);
});
EOF
printf 'globalThis.__preloaded = true;\n' >setup.js
printf '[test]\npreload = ["./setup.js"]\n' >bunfig.toml
"$BUN" test --coverage --coverage-reporter=lcov >test.log 2>&1 ||
    fail "bun test: $(cat test.log)"
grep -q ' 3 pass' test.log || fail "expected 3 passing tests"
grep -q 'SF:packages/util/index.js' coverage/lcov.info || fail "lcov output"
ok "bun test: mock(), globals, preload, lcov coverage (3 pass)"
cp packages/util/index.js index.orig
sed 's/toLowerCase()/toUpperCase()/' index.orig >packages/util/index.js
if "$BUN" test >/dev/null 2>&1; then
    fail "tests did not detect the mutation"
fi
cp index.orig packages/util/index.js
ok "mutated slug() fails the suite"

# 6. Bundling for the Node consumer keeps the output runnable on node.
"$BUN" build packages/app/index.js --target=node --outdir=dist >/dev/null 2>&1 ||
    fail "bun build"
"$NODE" dist/index.js | grep -q '^hello-world (node ' || fail "bundle on node"
ok "bun build --target=node output runs on node"

# 7. A new Bun workspace project defaults to the isolated linker.
cp -R "$ROOT/fixture" "$WORK/fresh"
cd "$WORK/fresh"
"$BUN" install >/dev/null 2>&1 || fail "bun install on fresh fixture"
grep -q '"configVersion": 1' bun.lock || fail "fresh configVersion"
[ -d node_modules/.bun ] || fail "isolated store missing"
ok "fresh workspace installs isolated (configVersion 1, node_modules/.bun)"
cd packages/app
"$NODE" -e "import('native-dep/package.json', {with: {type: 'json'}})" ||
    fail "root dependency not visible"
ok "isolated linker still exposes root dependencies to workspace packages"

echo "$PASS checks passed"
