#!/usr/bin/env sh
# Verifies the lineup example plugin in a disposable copy (helptags writes
# doc/tags, so the skill directory is never modified).
#
#   sh verify.sh          all checks below (default)
#   sh verify.sh pure     util_spec.lua under PUC Lua and under nvim -l;
#                         rockspec structure under PUC Lua
#   sh verify.sh suite    headless suite on the correct plugin
#   sh verify.sh mutants  same suite on each mutants/*.patch; each must fail
#                         with the test named on its "Expect:" line
#   sh verify.sh startup  --startuptime: count require('lineup...') lines
#   sh verify.sh demos    demos/*.lua: API facts the cards quote
#   sh verify.sh package  runtime directories only, on a clean runtimepath
#
# NVIM and LUA override the executables. A missing executable prints SKIP
# and does not fail; a check that runs and fails exits 1.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-all}
case "$MODE" in
    all | pure | suite | mutants | startup | demos | package) ;;
    *)
        echo 'usage: verify.sh [all|pure|suite|mutants|startup|demos|package]' >&2
        exit 2
        ;;
esac
NVIM=${NVIM:-$(command -v nvim || true)}
LUA=${LUA:-$(command -v lua || true)}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
# Isolate from the user's config, data, state, and cache.
export XDG_CONFIG_HOME="$WORK/xdg/config" XDG_DATA_HOME="$WORK/xdg/data"
export XDG_STATE_HOME="$WORK/xdg/state" XDG_CACHE_HOME="$WORK/xdg/cache"

fail() {
    echo "FAIL $1" >&2
    exit 1
}

have_nvim() {
    if [ -z "$NVIM" ] || [ ! -x "$NVIM" ]; then
        echo "SKIP $1: nvim not found (set NVIM=/path/to/nvim)"
        return 1
    fi
}

have_patch() {
    command -v patch >/dev/null 2>&1 && return 0
    echo "SKIP $1: patch not found"
    return 1
}

# fresh DIR: copy the plugin to DIR
fresh() {
    rm -rf "$1"
    cp -R "$ROOT/lineup" "$1"
}

# suite DIR LOG: run the headless suite; returns its exit status
suite_in() {
    (cd "$1" && "$NVIM" --clean --headless -u tests/minimal_init.lua \
        -l tests/run.lua) >"$2" 2>&1
}

pure() {
    fresh "$WORK/pure"
    if [ -n "$LUA" ]; then
        "$LUA" "$WORK/pure/tests/util_spec.lua" | tail -n 1
        "$LUA" "$WORK/pure/tests/rockspec_check.lua"
    else
        echo 'SKIP pure/lua: lua not found (set LUA=/path/to/lua)'
    fi
    if have_nvim pure/nvim; then
        "$NVIM" --clean -l "$WORK/pure/tests/util_spec.lua" 2>&1 |
            tail -n 1
    fi
    # lua54-only.patch uses table.unpack: PUC Lua accepts it, LuaJIT does not.
    [ -n "$LUA" ] && [ -n "$NVIM" ] && [ -x "$NVIM" ] || return 0
    have_patch pure/lua54-only || return 0
    patch -s -p1 -d "$WORK/pure" <"$ROOT/mutants/lua54-only.patch"
    "$LUA" "$WORK/pure/tests/util_spec.lua" >/dev/null ||
        fail 'lua54-only: expected PUC Lua to accept table.unpack'
    if "$NVIM" --clean -l "$WORK/pure/tests/util_spec.lua" \
        >"$WORK/pure.log" 2>&1; then
        fail 'lua54-only: nvim accepted table.unpack'
    fi
    echo "lua54-only: passes under $("$LUA" -v 2>&1 | cut -d' ' -f1-2)," \
        "fails under nvim: $(grep -o "attempt to call field 'unpack'.*" \
            "$WORK/pure.log" | head -n 1)"
}

suite() {
    have_nvim suite || return 0
    "$NVIM" --version | head -n 1
    fresh "$WORK/suite"
    suite_in "$WORK/suite" "$WORK/suite.log" || {
        cat "$WORK/suite.log" >&2
        fail 'suite on the correct plugin'
    }
    grep -E '^(ok|  )' "$WORK/suite.log"
    tail -n 1 "$WORK/suite.log"
}

mutants() {
    have_nvim mutants || return 0
    have_patch mutants || return 0
    for p in "$ROOT"/mutants/*.patch; do
        name=$(basename "$p" .patch)
        expect=$(sed -n 's/^Expect: //p' "$p")
        dir="$WORK/m-$name"
        fresh "$dir"
        patch -s -p1 -d "$dir" <"$p" || fail "$name: patch does not apply"
        if suite_in "$dir" "$dir.log"; then
            fail "$name: suite passed on a mutant"
        fi
        want=${expect#FAIL }
        # "failed: a | b" is printed by run.lua after all tests ran.
        failed=$(sed -n 's/^failed: //p' "$dir.log")
        case " | $failed | " in
            *" | $want | "*) ;;
            *)
                cat "$dir.log" >&2
                fail "$name: expected '$want' in failed list"
                ;;
        esac
        n=$(printf '%s\n' "$failed" | awk -F ' [|] ' '{print NF}')
        echo "killed $name: $n failing test(s), including '$want'"
    done
}

# requires DIR LOG: startup with the plugin; print require('lineup') count
requires() {
    (cd "$1" && "$NVIM" --clean --headless -u tests/minimal_init.lua \
        --startuptime "$2" +qa)
    grep -c "require('lineup" "$2" || true
}

startup() {
    have_nvim startup || return 0
    have_patch startup || return 0
    fresh "$WORK/lazy"
    lazy=$(requires "$WORK/lazy" "$WORK/lazy.log")
    [ "$lazy" -eq 0 ] || fail "lazy plugin required lineup $lazy time(s)"
    fresh "$WORK/eager"
    patch -s -p1 -d "$WORK/eager" <"$ROOT/mutants/eager-require.patch"
    eager=$(requires "$WORK/eager" "$WORK/eager.log")
    [ "$eager" -gt 0 ] || fail 'eager mutant did not require lineup'
    echo "startup require('lineup...') lines: lazy=$lazy eager=$eager"
    for kind in lazy eager; do
        # self+sourced ms of plugin/lineup.lua (machine-specific, noisy)
        ms=$(grep 'plugin/lineup.lua' "$WORK/$kind.log" | awk '{print $2}')
        echo "  $kind plugin/lineup.lua self+sourced: $ms ms"
    done
}

demos() {
    have_nvim demos || return 0
    mkdir -p "$WORK/demos"
    for f in "$ROOT"/demos/*.lua; do
        echo "## $(basename "$f")"
        (cd "$WORK/demos" && "$NVIM" --clean --headless -l "$f") 2>&1 ||
            fail "demo $(basename "$f")"
    done
}

package() {
    have_nvim package || return 0
    fresh "$WORK/src"
    mkdir -p "$WORK/pkg/lineup"
    for d in plugin lua ftplugin doc; do
        cp -R "$WORK/src/$d" "$WORK/pkg/lineup/$d"
    done
    "$NVIM" --clean --headless --cmd "set rtp^=$WORK/pkg/lineup" \
        -l "$WORK/src/tests/installed_check.lua" 2>&1 ||
        fail 'installed layout'
}

case "$MODE" in
    pure) pure ;;
    package) package ;;
    demos) demos ;;
    suite) suite ;;
    mutants) mutants ;;
    startup) startup ;;
    all)
        pure
        suite
        mutants
        startup
        demos
        package
        ;;
esac
echo "VERIFY DONE: $MODE"
