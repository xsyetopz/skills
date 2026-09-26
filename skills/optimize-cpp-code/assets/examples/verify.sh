#!/usr/bin/env sh
# Builds and runs the C++ construct catalog in a disposable directory so
# the skill directory never receives binaries or assembly files.
#
#   sh verify.sh verify      equivalence + allocation/copy/move/flush
#                            oracles, and identical stdout from printers
#   sh verify.sh benchmark   run every pair once (smoke; no timing)
#   sh verify.sh asm         assert atomics, indirect calls, guards, and
#                            bounds-check traps in the emitted assembly
#   sh verify.sh diagnose    expected compiler diagnostics
#   sh verify.sh time [F]    std::chrono median timing of pairs matching F
#   sh verify.sh io          hyperfine over the stdout printers
#   sh verify.sh sanitize    ASan+UBSan build of verify; dangling view
#   sh verify.sh hardening   libc++ hardening none vs fast
#   sh verify.sh parallel    std::execution::par vs sequential
#
# CXX overrides the compiler (default c++). On macOS, if the default SDK
# cannot link, the newest SDK under the Command Line Tools that compiles
# and links a probe using <flat_map>, <print>, and <memory_resource> is
# used; the chosen SDKROOT is printed.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | asm | diagnose | time | io | sanitize | hardening | parallel) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|asm|diagnose|time [filter]|io|sanitize|hardening|parallel]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
CXX=${CXX:-c++}
STD='-std=c++23'
WARN='-Wall -Wextra -Werror -Wno-pessimizing-move -Wno-redundant-move'
SRC="$ROOT/constructs"
ALONE="$ROOT/standalone"

cat >"$WORK/probe.cpp" <<'EOF'
#include <flat_map>
#include <memory_resource>
#include <print>
#include <span>
#include <version>
int main() {
  std::flat_map<int, int> m;
  m[1] = _LIBCPP_VERSION;
  std::print("{}\n", m[1]);
}
EOF
links() {
    "$CXX" "$STD" "$WORK/probe.cpp" -o "$WORK/probe" >/dev/null 2>&1
}
if ! links; then
    found=''
    if [ -d /Library/Developer/CommandLineTools/SDKs ]; then
        sdks=$(printf '%s\n' /Library/Developer/CommandLineTools/SDKs/MacOSX[0-9]*.sdk |
            sort -r -V)
        for sdk in $sdks; do
            SDKROOT=$sdk
            export SDKROOT
            if links; then
                found=$sdk
                break
            fi
        done
    fi
    if [ -z "$found" ]; then
        echo 'no SDK links the probe (needs libc++ with <flat_map>, <print>)' >&2
        exit 1
    fi
fi
"$CXX" --version
echo "SDKROOT=${SDKROOT:-<default>}"
echo "_LIBCPP_VERSION=$("$WORK/probe")"

BIN="$WORK/constructs"
build() {
    # shellcheck disable=SC2086 # word splitting of flag lists is intended
    "$CXX" "$STD" -O2 $WARN -I"$SRC" "$SRC"/*.cpp -o "$BIN"
}

# count FILE FUNCTION REGEX: matching lines inside one function's assembly
# (Mach-O prefixes C symbols with an underscore; ELF does not).
count() {
    awk -v name="$2" '
        $0 ~ "^_?" name ":" { on = 1 }
        on { print }
        on && /\.cfi_endproc/ { exit }
    ' "$1" | grep -cE "$3" || true
}

# expect FILE FUNCTION REGEX some|none
expect() {
    n=$(count "$1" "$2" "$3")
    lines=$(count "$1" "$2" '.')
    if [ "$lines" -eq 0 ]; then
        echo "ASM $2: symbol not found" >&2
        exit 1
    fi
    echo "ASM $2: $n line(s) match /$3/"
    case "$4" in
        some) [ "$n" -gt 0 ] || { echo "expected /$3/ in $2" >&2; exit 1; } ;;
        none) [ "$n" -eq 0 ] || { echo "unexpected /$3/ in $2" >&2; exit 1; } ;;
    esac
}

asm_of() {
    # shellcheck disable=SC2086
    "$CXX" "$STD" -O2 $WARN -I"$SRC" -S "$SRC/$1.cpp" -o "$WORK/$1.s"
    echo "$WORK/$1.s"
}

case "$MODE" in
    verify)
        build
        "$BIN" verify
        a=$("$BIN" print-endl 2000 | cksum)
        for m in newline nosync printf print format-to; do
            b=$("$BIN" "print-$m" 2000 | cksum)
            [ "$a" = "$b" ] || { echo "print-$m: output differs" >&2; exit 1; }
        done
        echo "stdout: identical bytes from all printers ($a)"
        ;;
    benchmark)
        build
        "$BIN" smoke
        ;;
    asm)
        case $(uname -m) in
            arm64 | aarch64) ;;
            *)
                echo "NOT ASSERTED on $(uname -m): patterns are aarch64 only"
                exit 0
                ;;
        esac
        # Recorded with Apple clang 21 (swift.org 6.3.3 toolchain), libc++
        # 21.1, -O2, arm64 (LSE atomics: ldadd*, RCpc: ldapr).
        O=$(asm_of objects)
        A='ldadd|ldxr|stxr|cas|swp'
        expect "$O" shared_by_value_baseline "$A" some
        expect "$O" shared_by_ref_candidate "$A" none
        expect "$O" shared_handoff_baseline "$A" some
        expect "$O" unique_handoff_candidate "$A" none
        G=$(asm_of codegen)
        expect "$G" virtual_total_baseline 'blr' some
        expect "$G" template_total_candidate 'blr' none
        expect "$G" crtp_total_candidate 'blr' none
        expect "$G" nonfinal_area_baseline 'blr|br[[:space:]]' some
        expect "$G" final_area_candidate 'blr|br[[:space:]]' none
        expect "$G" apply_function_baseline 'blr' some
        expect "$G" apply_template_candidate 'blr' none
        expect "$G" crc_static_baseline '__cxa_guard' some
        expect "$G" crc_constexpr_candidate '__cxa_guard' none
        expect "$G" variant_index_candidate 'blr' none
        # Recorded, not asserted: whether libc++ std::visit and the
        # consteval switch compile to an indirect call on this toolchain.
        echo "ASM variant_total_candidate: $(count "$G" variant_total_candidate 'blr') blr"
        echo "ASM route_runtime_baseline: $(count "$G" route_runtime_baseline 'bl[[:space:]]') bl"
        echo "ASM route_consteval_candidate: $(count "$G" route_consteval_candidate 'bl[[:space:]]') bl"
        C=$(asm_of concurrency)
        expect "$C" bump_seq_cst_baseline 'ldaddal' some
        expect "$C" bump_relaxed_candidate 'ldaddal' none
        expect "$C" bump_relaxed_candidate 'ldadd[[:space:]]' some
        echo "ASM read_seq_cst_baseline: $(count "$C" read_seq_cst_baseline 'ldar[[:space:]]') ldar"
        echo "ASM read_acquire_candidate: $(count "$C" read_acquire_candidate 'ldapr') ldapr"
        echo "ASM publish_seq_cst_baseline: $(count "$C" publish_seq_cst_baseline 'stlr') stlr"
        echo "ASM publish_release_candidate: $(count "$C" publish_release_candidate 'stlr') stlr"
        echo 'ASM PASSED'
        ;;
    diagnose)
        out=$("$CXX" "$STD" -Wpessimizing-move -Wredundant-move -fsyntax-only \
            -I"$SRC" "$SRC/objects.cpp" 2>&1 || true)
        printf '%s\n' "$out" | grep -E 'warning:' || true
        for w in 'moving a temporary object prevents copy elision' \
            'moving a local object in a return statement prevents copy elision' \
            'redundant move in return statement'; do
            printf '%s' "$out" | grep -q "$w" || {
                echo "missing diagnostic: $w" >&2
                exit 1
            }
        done
        if "$CXX" "$STD" -fsyntax-only "$ALONE/consteval_error.cpp" \
            2>"$WORK/consteval.txt"; then
            echo 'consteval_error.cpp compiled; expected an error' >&2
            exit 1
        fi
        grep -m1 'error:' "$WORK/consteval.txt"
        dw=$("$CXX" "$STD" -fsyntax-only "$ALONE/dangling.cpp" 2>&1 || true)
        printf '%s\n' "$dw" | grep -m1 'warning:' || echo 'dangling.cpp: no compiler warning'
        echo 'DIAGNOSE PASSED'
        ;;
    time)
        build
        "$BIN" time "${2:-}"
        ;;
    io)
        build
        if command -v hyperfine >/dev/null 2>&1; then
            hyperfine --warmup 3 -N --output=pipe \
                "$BIN print-endl 200000" \
                "$BIN print-newline 200000" \
                "$BIN print-nosync 200000" \
                "$BIN print-printf 200000" \
                "$BIN print-print 200000" \
                "$BIN print-format-to 200000"
        else
            echo 'hyperfine not installed: printers not timed'
        fi
        ;;
    sanitize)
        # -O1 keeps reports readable. ASan interposes operator new, so
        # allocations inside libc++.dylib are not counted; the equality
        # oracles still run, the count assertions are switched off.
        # shellcheck disable=SC2086
        "$CXX" "$STD" -O1 -g $WARN -fsanitize=address,undefined \
            -fno-omit-frame-pointer -fno-sanitize-recover=undefined \
            -I"$SRC" "$SRC"/*.cpp -o "$BIN"
        CONSTRUCTS_NO_COUNTS=1 "$BIN" verify >/dev/null
        echo 'SANITIZE verify: no ASan/UBSan report (count checks off)'
        "$CXX" "$STD" -O1 -g -fsanitize=address -fno-omit-frame-pointer \
            -w "$ALONE/dangling.cpp" -o "$WORK/dangling"
        if "$WORK/dangling" >/dev/null 2>"$WORK/asan.txt"; then
            echo 'dangling.cpp ran clean; expected an ASan report' >&2
            exit 1
        fi
        grep -m1 -E 'ERROR: AddressSanitizer: [a-z-]+' "$WORK/asan.txt"
        echo 'SANITIZE PASSED'
        ;;
    hardening)
        for m in NONE FAST; do
            "$CXX" "$STD" -O2 -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_$m \
                "$ALONE/hardening.cpp" -o "$WORK/hard_$m"
            "$CXX" "$STD" -O2 -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_$m \
                -S "$ALONE/hardening.cpp" -o "$WORK/hard_$m.s"
            "$WORK/hard_$m" sum 10 >/dev/null
        done
        case $(uname -m) in
            arm64 | aarch64)
                expect "$WORK/hard_NONE.s" gather_sum 'brk' none
                expect "$WORK/hard_FAST.s" gather_sum 'brk' some
                ;;
        esac
        status=0
        "$WORK/hard_FAST" oob >/dev/null 2>&1 || status=$?
        [ "$status" -ne 0 ] || { echo 'FAST mode did not trap' >&2; exit 1; }
        echo "HARDENING FAST oob: trapped (exit status $status)"
        if command -v hyperfine >/dev/null 2>&1; then
            hyperfine --warmup 3 -N \
                "$WORK/hard_NONE sum 20000" "$WORK/hard_FAST sum 20000"
        fi
        ;;
    parallel)
        "$CXX" "$STD" -O2 -fexperimental-library "$ALONE/parallel.cpp" \
            -o "$WORK/parallel"
        "$WORK/parallel"
        ;;
esac
