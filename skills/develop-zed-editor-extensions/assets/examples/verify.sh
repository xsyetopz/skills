#!/usr/bin/env sh
# Verifies every example extension without Zed.
#
#   sh verify.sh fetch   network: cargo deps, pinned grammar, Zed schemas
#   sh verify.sh         offline: wasm builds, API version, unit tests,
#                        clippy, manifest/query/theme checks, mutants,
#                        and `tree-sitter query` when the CLI is on PATH
#
# Environment: PYTHON (3.11+), TREE_SITTER (CLI path), ZED_EXT_CACHE
# (defaults to ~/.cache/develop-zed-editor-extensions). Build output goes
# to the cache, never into this directory.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SCRIPTS=$(CDPATH='' cd -- "$ROOT/../../scripts" && pwd)
MODE=${1:-check}
PYTHON=${PYTHON:-python3}
CACHE=${ZED_EXT_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/develop-zed-editor-extensions}
CRATES="marksman-lsp mcp-server-memory lldb-dap-debugger"
FIXTURES="makefile marksman-lsp mcp-server-memory lldb-dap-debugger"
FIXTURES="$FIXTURES ember-theme mono-icons"
GRAMMAR_URL=https://github.com/tree-sitter-grammars/tree-sitter-make
GRAMMAR_REV=5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d
GRAMMAR="$CACHE/tree-sitter-make-$GRAMMAR_REV"
THEME_SCHEMA="$CACHE/themes-v0.2.0.json"
ICON_SCHEMA="$CACHE/icon_themes-v0.3.0.json"
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

# Zed builds with the `rustc` on PATH. A Homebrew rustc next to a rustup
# toolchain has no wasm32-wasip2 sysroot even after `rustup target add`.
use_wasm_toolchain() {
    libdir=$(rustc --print target-libdir --target wasm32-wasip2 2>/dev/null) ||
        libdir=""
    if [ -z "$libdir" ] || [ ! -d "$libdir" ]; then
        command -v rustup >/dev/null 2>&1 ||
            fail "rustc lacks wasm32-wasip2 and rustup is unavailable"
        toolchain_bin=$(dirname "$(rustup which rustc)")
        PATH="$toolchain_bin:$PATH"
        export PATH
        libdir=$(rustc --print target-libdir --target wasm32-wasip2)
        [ -d "$libdir" ] || fail "run: rustup target add wasm32-wasip2"
    fi
    echo "rustc $(rustc --version | cut -d' ' -f2) at $(command -v rustc)"
}

fetch() {
    mkdir -p "$CACHE"
    for crate in $CRATES; do
        cargo fetch --locked --manifest-path "$ROOT/$crate/Cargo.toml"
    done
    if [ ! -f "$GRAMMAR/src/node-types.json" ]; then
        rm -rf "$GRAMMAR"
        git init -q "$GRAMMAR"
        git -C "$GRAMMAR" fetch -q --depth 1 "$GRAMMAR_URL" "$GRAMMAR_REV"
        git -C "$GRAMMAR" checkout -q FETCH_HEAD
    fi
    curl -fsSL -o "$THEME_SCHEMA" https://zed.dev/schema/themes/v0.2.0.json
    curl -fsSL -o "$ICON_SCHEMA" \
        https://zed.dev/schema/icon_themes/v0.3.0.json
    echo "cache ready: $CACHE"
}

# macOS SDKs whose .tbd stubs the linker cannot read break cc links; try
# the default SDK first, then each installed SDK.
tree_sitter_query() {
    TREE_SITTER_LIBDIR="$CACHE/tree-sitter-lib" "$TREE_SITTER" query \
        -p "$GRAMMAR" "$1" "$ROOT/samples/Makefile" 2>&1
}

run_tree_sitter() {
    TREE_SITTER=${TREE_SITTER:-$(command -v tree-sitter || true)}
    if [ -z "$TREE_SITTER" ]; then
        echo "SKIP tree-sitter query: no tree-sitter CLI (set TREE_SITTER)"
        return
    fi
    for query in "$ROOT"/makefile/languages/makefile/*.scm; do
        name=$(basename "$query")
        if ! out=$(tree_sitter_query "$query"); then
            for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.sdk; do
                [ -d "$sdk" ] || continue
                if out=$(SDKROOT=$sdk tree_sitter_query "$query"); then
                    echo "note SDKROOT=$sdk"
                    SDKROOT=$sdk
                    export SDKROOT
                    break
                fi
            done
        fi
        echo "$out" | grep -q 'capture:' ||
            fail "tree-sitter query $name: $(echo "$out" | tail -n 3)"
        count=$(echo "$out" | grep -c 'capture:')
        ok "tree-sitter $("$TREE_SITTER" --version | cut -d' ' -f2): $name, $count captures"
    done
}

expect_error() {
    label=$1
    shift
    if "$@" >"$WORK/mutant.log" 2>&1; then
        fail "$label: checker accepted a broken fixture"
    fi
    grep -q "$MATCH" "$WORK/mutant.log" ||
        fail "$label: unexpected output: $(cat "$WORK/mutant.log")"
    ok "mutant rejected: $label"
}

check() {
    [ -f "$GRAMMAR/src/node-types.json" ] && [ -f "$THEME_SCHEMA" ] ||
        fail "cache missing; run: sh verify.sh fetch"
    WORK=$(mktemp -d)
    trap 'rm -rf "$WORK"' 0
    trap 'exit 130' INT
    trap 'exit 143' TERM
    "$PYTHON" -c 'import tomllib' 2>/dev/null ||
        fail "PYTHON=$PYTHON must be Python 3.11+ (the checkers need tomllib)"
    use_wasm_toolchain
    for crate in $CRATES; do
        manifest="$ROOT/$crate/Cargo.toml"
        cargo build -q --release --offline --locked --target wasm32-wasip2 \
            --manifest-path "$manifest" --target-dir "$CACHE/target" ||
            fail "cargo build $crate"
        wasm="$CACHE/target/wasm32-wasip2/release/$(echo "$crate" | tr - _).wasm"
        version=$("$PYTHON" "$SCRIPTS/wasm_api_version.py" "$wasm" --max 0.7.0) ||
            fail "api version of $crate"
        ok "$crate: wasm32-wasip2 build, $version, $(wc -c <"$wasm" | tr -d ' ') B"
        cargo test -q --offline --locked --manifest-path "$manifest" \
            --target-dir "$CACHE/target" >"$WORK/test.log" 2>&1 ||
            fail "cargo test $crate: $(tail -n 20 "$WORK/test.log")"
        ok "$crate: $(grep 'test result' "$WORK/test.log" | head -n 1)"
        if cargo clippy --version >/dev/null 2>&1; then
            cargo clippy -q --offline --locked --target wasm32-wasip2 \
                --manifest-path "$manifest" --target-dir "$CACHE/target" \
                -- -D warnings || fail "cargo clippy $crate"
            ok "$crate: cargo clippy -D warnings (wasm32-wasip2)"
        else
            echo "SKIP cargo clippy: not installed"
        fi
    done
    for fixture in $FIXTURES; do
        "$PYTHON" "$SCRIPTS/check_extension.py" --registry "$ROOT/$fixture" \
            >"$WORK/ext.log" 2>&1 || fail "check_extension $fixture: $(cat "$WORK/ext.log")"
        ok "$fixture: check_extension --registry: $(tail -n 1 "$WORK/ext.log")"
    done
    "$PYTHON" "$SCRIPTS/check_queries.py" "$ROOT/makefile/languages/makefile" \
        --node-types "$GRAMMAR/src/node-types.json" >"$WORK/q.log" 2>&1 ||
        fail "check_queries: $(cat "$WORK/q.log")"
    ok "makefile queries: $(tail -n 1 "$WORK/q.log")"
    "$PYTHON" "$SCRIPTS/check_theme.py" "$ROOT/ember-theme/themes/ember.json" \
        --schema "$THEME_SCHEMA" >"$WORK/t.log" 2>&1 ||
        fail "theme: $(cat "$WORK/t.log")"
    ok "ember theme vs themes/v0.2.0.json: $(tail -n 1 "$WORK/t.log")"
    "$PYTHON" "$SCRIPTS/check_theme.py" \
        "$ROOT/mono-icons/icon_themes/mono-icons.json" \
        --schema "$ICON_SCHEMA" --root "$ROOT/mono-icons" >"$WORK/i.log" 2>&1 ||
        fail "icon theme: $(cat "$WORK/i.log")"
    ok "mono icons vs icon_themes/v0.3.0.json: $(tail -n 1 "$WORK/i.log")"

    cp -R "$ROOT/makefile" "$WORK/m"
    printf '\n[language-servers.x]\nlanguages = ["Makefile"]\n' \
        >>"$WORK/m/extension.toml"
    MATCH="did you mean \`language_servers\`"
    expect_error "hyphenated [language-servers] table" \
        "$PYTHON" "$SCRIPTS/check_extension.py" "$WORK/m"
    rm -rf "$WORK/m" && cp -R "$ROOT/makefile" "$WORK/m"
    sed "s/^rev = .*/rev = \"main\"/" "$ROOT/makefile/extension.toml" \
        >"$WORK/m/extension.toml"
    MATCH="40-character commit SHA"
    expect_error "grammar pinned to a branch" \
        "$PYTHON" "$SCRIPTS/check_extension.py" "$WORK/m"
    rm -rf "$WORK/m" && cp -R "$ROOT/makefile" "$WORK/m"
    sed 's/(targets) @name/(target) @name/' \
        "$ROOT/makefile/languages/makefile/outline.scm" \
        >"$WORK/m/languages/makefile/outline.scm"
    MATCH="no named node \`target\`"
    expect_error "outline node missing from the pinned grammar" \
        "$PYTHON" "$SCRIPTS/check_queries.py" "$WORK/m/languages/makefile" \
        --node-types "$GRAMMAR/src/node-types.json"
    sed 's/"#e5484d"/"crimson"/' "$ROOT/ember-theme/themes/ember.json" \
        >"$WORK/bad-theme.json"
    MATCH="bad color 'crimson'"
    expect_error "named color in a theme" \
        "$PYTHON" "$SCRIPTS/check_theme.py" "$WORK/bad-theme.json" \
        --schema "$THEME_SCHEMA"

    for test in "$SCRIPTS"/test_*.py; do
        "$PYTHON" "$test" >"$WORK/unit.log" 2>&1 ||
            fail "$(basename "$test"): $(tail -n 20 "$WORK/unit.log")"
        ok "$(basename "$test"): $(grep '^Ran' "$WORK/unit.log")"
    done
    run_tree_sitter
    echo "$PASS checks passed"
}

case "$MODE" in
    fetch) fetch ;;
    check) check ;;
    *)
        echo "usage: verify.sh [fetch|check]" >&2
        exit 2
        ;;
esac
