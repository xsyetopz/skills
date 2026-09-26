#!/usr/bin/env sh
# Exercises every construct card against the bundled extension in a
# disposable copy, so node_modules/, dist/, out/, and .vsix files never
# land in the skill directory.
#
#   sh verify.sh [offline]   type checks, unit tests, bundles, manifest
#                            rules, vsce ls/package, isolated VSIX install
#   sh verify.sh network     downloads VS Code with @vscode/test-electron
#                            and runs the extension-host suites
#
# offline needs the npm registry once to fill the Bun cache; later runs
# resolve from the cache. BUN, NODE, PYTHON, and CODE (a VS Code CLI used
# only with private --user-data-dir/--extensions-dir) override tools.
# VSCODE_TEST_VERSION picks the downloaded build (default: stable).
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CHECK="$ROOT/../../scripts/check_manifest.py"
MODE=${1:-offline}
case "$MODE" in
    offline | network) ;;
    *)
        echo 'usage: verify.sh [offline|network]' >&2
        exit 2
        ;;
esac
BUN=${BUN:-bun}
NODE=${NODE:-node}
PYTHON=${PYTHON:-python3}
CODE=${CODE:-code}
CACHE=${SKILLS_CACHE_DIR:-$HOME/.cache/xsyetopz-skills}
export BUN_INSTALL_CACHE_DIR="${BUN_INSTALL_CACHE_DIR:-$CACHE/bun}"
# mktemp -d keeps the path short enough for VS Code's IPC socket.
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
echo "bun $("$BUN" --version), node $("$NODE" --version)"

EXT="$WORK/ext"
L="$WORK/logs" # logs and backups stay out of the packaged tree
mkdir -p "$L"
cp -R "$ROOT/extension" "$EXT"
cd "$EXT"
"$BUN" install --frozen-lockfile >"$L/install.log" 2>&1 ||
    fail "bun install: $(cat "$L/install.log")"
echo "tsc $("$BUN" x tsc --version), vsce $("$BUN" x vsce --version)"
"$BUN" x esbuild --version >/dev/null

if [ "$MODE" = network ]; then
    "$BUN" x tsc -p tsconfig.test.json || fail "compile host tests"
    "$BUN" esbuild.mjs || fail "bundle"
    VERSION=${VSCODE_TEST_VERSION:-stable}
    mkdir -p "$CACHE/vscode-test"
    "$NODE" -e '
const { downloadAndUnzipVSCode } = require("@vscode/test-electron");
downloadAndUnzipVSCode({ version: process.argv[1], cachePath: process.argv[2] })
  .then((p) => console.log(p), (e) => { console.error(e); process.exit(1); });
' "$VERSION" "$CACHE/vscode-test" >"$L/download.log" 2>&1 ||
        fail "download VS Code: $(tail -n 5 "$L/download.log")"
    EXE=$(tail -n 1 "$L/download.log")
    [ -x "$EXE" ] || fail "no VS Code executable: $EXE"
    echo "VS Code executable: $EXE"
    T="$WORK/h"
    mkdir -p "$T/ws-t" "$T/ws-u/.vscode" "$T/u/u/User"
    printf '[user]\n\tname = Test Owner\n' >"$T/gitconfig"
    printf '{ "todoOwner.gitPath": "/nonexistent/evil-git" }\n' \
        >"$T/ws-u/.vscode/settings.json"
    printf '{ "security.workspace.trust.startupPrompt": "never" }\n' \
        >"$T/u/u/User/settings.json"

    TODO_OWNER_TMP="$T" VSCODE_TEST_EXECUTABLE="$EXE" \
        "$BUN" x vscode-test >"$L/host.log" 2>&1 ||
        fail "trusted host suite: $(tail -n 30 "$L/host.log")"
    grep -q '6 passing' "$L/host.log" || fail "expected 6 passing host tests"
    ok "extension host (trusted): 6 passing"
    grep -rq "activationEvent: 'onCommand:todoOwner.clearApiToken'" \
        "$T/t/u/logs" || fail "implicit onCommand activation not logged"
    ok "exthost.log: activated by onCommand with activationEvents: []"
    find "$T/t/u/logs" -path '*skills-example.todo-owner*' \
        -name 'TODO Owner.log' -exec grep -q 'activated in desktop' {} + ||
        fail "LogOutputChannel file missing"
    ok "LogOutputChannel wrote exthost/skills-example.todo-owner/TODO Owner.log"
    if grep -rq 'document selector without scheme' "$T/t/u/logs"; then
        fail "host warned about a selector without scheme"
    fi
    ok "no 'document selector without scheme' warning"

    # runTests() always adds --disable-workspace-trust, so Restricted Mode
    # needs a direct launch with --extensionTestsPath.
    GIT_CONFIG_GLOBAL="$T/gitconfig" "$EXE" \
        --extensionDevelopmentPath="$EXT" \
        --extensionTestsPath="$EXT/out/test/untrusted/index.js" \
        --user-data-dir="$T/u/u" --extensions-dir="$T/u/x" \
        --disable-extensions --skip-welcome --skip-release-notes \
        --disable-updates --use-inmemory-secretstorage --disable-keytar \
        --no-sandbox --disable-gpu-sandbox "$T/ws-u" >"$L/untrusted.log" 2>&1 ||
        fail "untrusted run: $(grep -A6 Error "$L/untrusted.log" | head -20)"
    grep -q 'untrusted: 3 checks passed' "$L/untrusted.log" ||
        fail "untrusted checks did not report"
    ok "extension host (Restricted Mode): 3 checks passed"
    echo "$PASS checks passed"
    exit 0
fi

# 1. Types: the engines floor (1.74) compiles; floor - 1 does not.
"$BUN" x tsc --noEmit -p . || fail "tsc against @types/vscode 1.74.0"
ok "tsc --noEmit against @types/vscode 1.74.0"
cp package.json "$L/package.json"
cp bun.lock "$L/bun.lock"
"$BUN" add -d @types/vscode@1.73.1 >/dev/null 2>&1 || fail "add types 1.73.1"
if "$BUN" x tsc --noEmit -p . >"$L/tsc-old.log" 2>&1; then
    fail "code using LogOutputChannel compiled against 1.73.1"
fi
grep -q "no exported member named 'LogOutputChannel'" "$L/tsc-old.log" ||
    fail "unexpected tsc output: $(cat "$L/tsc-old.log")"
ok "@types/vscode 1.73.1 rejects LogOutputChannel (TS2724)"
cp "$L/package.json" package.json
cp "$L/bun.lock" bun.lock
"$BUN" install --frozen-lockfile >/dev/null 2>&1 || fail "restore install"

# 2. Pure logic runs under bun test without a VS Code host.
"$BUN" test test/unit >"$L/unit.log" 2>&1 ||
    fail "unit tests: $(cat "$L/unit.log")"
grep -q ' 12 pass' "$L/unit.log" || fail "expected 12 passing unit tests"
ok "bun test: 12 pass (findings, owner, trim, severity, stale guard)"
cp src/core.ts "$L/core.orig"
sed 's/(?!\\()//' "$L/core.orig" >src/core.ts
if "$BUN" test test/unit >/dev/null 2>&1; then
    fail "unit tests missed a mutated TODO pattern"
fi
cp "$L/core.orig" src/core.ts
ok "mutating the TODO(owner) lookahead fails the unit tests"

# 3. Bundles: one file per host, vscode external, no Node in the web one.
"$BUN" esbuild.mjs --production || fail "esbuild"
deps() { grep -o 'require("[^"]*")' "$1" | sort -u | tr '\n' ' '; }
[ "$(deps dist/node/extension.js)" = \
    'require("node:child_process") require("vscode") ' ] ||
    fail "node bundle requires: $(deps dist/node/extension.js)"
[ "$(deps dist/web/extension.js)" = 'require("vscode") ' ] ||
    fail "web bundle requires: $(deps dist/web/extension.js)"
ok "node bundle requires vscode + node:child_process; web only vscode"
if "$BUN" x esbuild src/extension.node.ts --bundle --platform=browser \
    --format=cjs --external:vscode --outfile="$L/web-bad.js" \
    >"$L/esb.log" 2>&1; then
    fail "browser bundle accepted node:child_process"
fi
grep -q 'Could not resolve "node:child_process"' "$L/esb.log" ||
    fail "unexpected esbuild output: $(cat "$L/esb.log")"
ok "platform=browser rejects the Node entry (node:child_process)"

# 4. Manifest rules, with sources and built entries.
"$PYTHON" "$CHECK" package.json --src src --built >"$L/check.log" ||
    fail "check_manifest: $(cat "$L/check.log")"
ok "check_manifest.py: $(tail -n 1 "$L/check.log")"

# 5. vsce: file list, .vscodeignore effect, package, validation errors.
"$BUN" x vsce ls --no-dependencies </dev/null >"$L/ls.log" 2>&1 ||
    fail "vsce ls: $(cat "$L/ls.log")"
[ "$(wc -l <"$L/ls.log" | tr -d ' ')" = 5 ] ||
    fail "vsce ls: $(cat "$L/ls.log")"
ok "vsce ls: 5 files ($(tr '\n' ' ' <"$L/ls.log"))"
: >"$L/empty.ignore"
all=$("$BUN" x vsce ls --no-dependencies --ignoreFile "$L/empty.ignore" \
    </dev/null | wc -l | tr -d ' ')
ok "without .vscodeignore vsce ls lists $all files (sources, tests, lock)"
"$BUN" x vsce package --no-dependencies -o "$L/todo-owner.vsix" </dev/null \
    >"$L/pkg.log" 2>&1 || fail "vsce package: $(cat "$L/pkg.log")"
entries=$("$PYTHON" -c 'import sys, zipfile
print(len(zipfile.ZipFile(sys.argv[1]).namelist()))' "$L/todo-owner.vsix")
ok "vsce package: todo-owner.vsix with $entries zip entries"
vsixmanifest() { unzip -p "$1" extension.vsixmanifest; }
vsixmanifest "$L/todo-owner.vsix" | grep -q '__web_extension' ||
    fail "browser entry did not tag the VSIX as a web extension"
ok "vsixmanifest tags: __web_extension (browser entry present)"
"$BUN" x vsce package --no-dependencies --pre-release -o "$L/pre.vsix" \
    </dev/null >/dev/null 2>&1 || fail "vsce package --pre-release"
vsixmanifest "$L/pre.vsix" |
    grep -q 'Code.PreRelease" Value="true"' || fail "PreRelease property"
ok "vsce package --pre-release sets Microsoft.VisualStudio.Code.PreRelease"
cp package.json "$L/package.json"
sed 's#"@types/vscode": "1.74.0"#"@types/vscode": "1.138.0"#' \
    "$L/package.json" >package.json
if "$BUN" x vsce ls --no-dependencies </dev/null >"$L/bad.log" 2>&1; then
    fail "vsce accepted @types/vscode newer than engines"
fi
grep -q 'greater than engines.vscode' "$L/bad.log" || fail "$(cat "$L/bad.log")"
ok "vsce rejects @types/vscode 1.138.0 with engines ^1.74.0"
cp "$L/package.json" package.json

# 6. Install the VSIX into a private profile; never the user's own.
if command -v "$CODE" >/dev/null 2>&1; then
    P="$WORK/p"
    "$CODE" --user-data-dir "$P/u" --extensions-dir "$P/x" \
        --install-extension "$L/todo-owner.vsix" >"$L/inst.log" 2>&1 ||
        fail "code --install-extension: $(cat "$L/inst.log")"
    "$CODE" --user-data-dir "$P/u" --extensions-dir "$P/x" \
        --list-extensions --show-versions >"$L/list.log" 2>&1
    grep -qx 'skills-example.todo-owner@0.2.0' "$L/list.log" ||
        fail "installed list: $(cat "$L/list.log")"
    ok "code --install-extension into a private profile: $(cat "$L/list.log")"
else
    echo "skip VSIX install: no VS Code CLI ($CODE)"
fi
echo "$PASS checks passed"
