#!/usr/bin/env sh
# Builds and runs the Rust construct catalog in a disposable copy so the
# skill directory never receives target/ or Criterion output.
#
#   sh verify.sh verify      equivalence + allocation/call-count oracles
#   sh verify.sh benchmark   run every pair once (smoke; no timing)
#   sh verify.sh asm         assert bounds checks, calls, atomics, SIMD in
#                            the emitted assembly
#   sh verify.sh time [F]    std-only Instant timing of pairs matching F
#   sh verify.sh profiles    build each [profile.*] card, print sizes
#   sh verify.sh ecosystem   rayon + rustc-hash oracles (fetches crates)
#   sh verify.sh measure     Criterion benchmarks (fetches crates);
#                            BENCH_FILTER selects, BENCH_OUT keeps reports
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | asm | time | profiles | ecosystem | measure) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|asm|time [filter]|profiles|ecosystem|measure]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs" "$ROOT/ecosystem" "$WORK/"
# Keep every artifact, including a user-configured build.build-dir, in the
# temporary copy.
CARGO_TARGET_DIR="$WORK/target"
CARGO_BUILD_BUILD_DIR="$WORK/target"
export CARGO_TARGET_DIR CARGO_BUILD_BUILD_DIR
C="$WORK/constructs/Cargo.toml"
E="$WORK/ecosystem/Cargo.toml"
BIN="$WORK/target/release/constructs"
rustc -V
build() {
    cargo build --quiet --locked --release --manifest-path "$C"
}

# count FUNCTION REGEX: matching lines inside one function's assembly.
count() {
    awk -v start="_$1:" -v alt="$1:" '
        $0 == start || $0 == alt { on = 1 }
        on { print }
        on && /\.cfi_endproc/ { exit }
    ' "$ASM" | grep -cE "$2" || true
}

# expect FUNCTION REGEX more|none: assert presence or absence.
expect() {
    n=$(count "$1" "$2")
    lines=$(count "$1" '.')
    if [ "$lines" -eq 0 ]; then
        echo "ASM $1: symbol not found" >&2
        exit 1
    fi
    echo "ASM $1: $n line(s) match /$2/"
    case "$3" in
        some) [ "$n" -gt 0 ] || { echo "expected /$2/ in $1" >&2; exit 1; } ;;
        none) [ "$n" -eq 0 ] || { echo "unexpected /$2/ in $1" >&2; exit 1; } ;;
    esac
}

case "$MODE" in
    verify)
        build
        "$BIN" verify
        # stdout cards: identical bytes from all three print paths.
        a=$("$BIN" print-baseline 2000 | cksum)
        for v in print-candidate print-buffered; do
            b=$("$BIN" "$v" 2000 | cksum)
            [ "$a" = "$b" ] || { echo "$v: output differs" >&2; exit 1; }
        done
        echo "stdout: identical output from all print paths ($a)"
        ;;
    benchmark)
        build
        "$BIN" smoke
        ;;
    asm)
        cargo rustc --quiet --locked --release --lib --manifest-path "$C" \
            -- --emit asm -C codegen-units=1
        ASM=$(ls "$WORK"/target/release/deps/constructs-*.s)
        # The "some" expectations were recorded with rustc 1.98.1 (LLVM
        # 22). If a baseline fails on another toolchain, that compiler
        # already removed the check: the card's safe rewrite is moot there.
        B=panic_bounds_check
        expect dot_index_baseline "$B" some
        expect dot_iter_candidate "$B" none
        expect add_index_baseline "$B" some
        expect add_reslice_candidate "$B" none
        expect words_index_baseline "$B" some
        expect words_chunks_candidate "$B" none
        expect gather_checked_baseline "$B" some
        expect gather_unchecked_candidate "$B" none
        # Any reference to the helper crate's `scale*` symbol (a direct
        # `bl` on aarch64, a GOT load plus `callq *%reg` on x86_64 PIC).
        expect scale_all_baseline 'helper[0-9]+scale' some
        expect scale_all_candidate 'helper[0-9]+scale' none
        case $(uname -m) in
            arm64 | aarch64)
                expect sum_f32_baseline 'fadd\.[0-9]+[hsd]' none
                expect sum_f32_candidate 'fadd\.[0-9]+[hsd]' some
                expect total_dyn_baseline 'blr' some
                expect total_generic_candidate 'blr' none
                expect total_enum_candidate 'blr' none
                A='ldadd|ldxr|stlxr|cas'
                expect arc_clone_baseline "$A" some
                expect arc_borrow_candidate "$A" none
                expect handles_arc_baseline "$A" some
                expect handles_rc_candidate "$A" none
                ;;
            *)
                echo "NOT ASSERTED on $(uname -m): SIMD, indirect-call, and"
                echo 'atomic patterns are written for aarch64 only.'
                ;;
        esac
        echo 'ASM PASSED'
        ;;
    time)
        build
        "$BIN" time "${2:-}"
        if command -v hyperfine >/dev/null 2>&1; then
            hyperfine --warmup 3 -N \
                "$BIN print-baseline 200000" \
                "$BIN print-candidate 200000" \
                "$BIN print-buffered 200000" \
                --output=null
        else
            echo 'hyperfine not installed: stdout-lock pair not timed'
        fi
        ;;
    profiles)
        for p in release release-cgu1 release-thin release-fat \
            release-abort release-size profiling; do
            cargo build --quiet --locked --manifest-path "$C" --profile "$p"
            size=$(wc -c <"$WORK/target/$p/constructs" | tr -d ' ')
            echo "PROFILE $p: $size bytes"
            eval "size_$(echo "$p" | tr - _)=$size"
        done
        # shellcheck disable=SC2154 # assigned through eval above
        [ "$size_release_abort" -lt "$size_release" ] || {
            echo 'panic=abort binary is not smaller than release' >&2
            exit 1
        }
        "$WORK/target/release-abort/constructs" verify >/dev/null
        echo 'PROFILES PASSED: release-abort still passes verify'
        ;;
    ecosystem)
        cargo run --quiet --locked --release --manifest-path "$E"
        ;;
    measure)
        cargo bench --quiet --locked --manifest-path "$E" --bench pairs -- \
            --warm-up-time 1 --measurement-time 2 ${BENCH_FILTER:+"$BENCH_FILTER"}
        if [ -n "${BENCH_OUT:-}" ]; then
            mkdir -p "$BENCH_OUT"
            cp -R "$WORK/target/criterion/." "$BENCH_OUT/"
            echo "Criterion reports: $BENCH_OUT"
        fi
        ;;
esac
