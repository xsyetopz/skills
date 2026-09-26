#!/usr/bin/env sh
# shellcheck disable=SC2086 # flag lists in CC/OPT/WARN are split on purpose
# Builds and runs the C construct catalog in a temporary directory, so no
# binaries, objects, profiles, or traces land in the skill directory.
#
#   sh verify.sh [verify]    oracles, allocation/write counts, C23 path,
#                            identical output from every emit variant
#   sh verify.sh benchmark   every pair once (smoke; no timing)
#   sh verify.sh sanitize    ASan+UBSan oracle run; UBSan must flag ub.c
#   sh verify.sh asm         assert instruction patterns in -S output
#   sh verify.sh remarks     assert loop-vectorize optimization records
#   sh verify.sh flags       LTO, ThinLTO, visibility, -mcpu, -O3, x86
#                            dispatch object
#   sh verify.sh pgo         IR and front-end PGO pipelines + hyperfine
#   sh verify.sh time [F]    clock_gettime medians for pairs matching F,
#                            hyperfine for the emit variants
#   sh verify.sh profile     leaks --atExit, sample, xctrace (macOS)
#
# Honors CC (default cc), CSTD (default c17), and OPT (default -O2) so the
# catalog can be built with the project's compiler and flags.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | sanitize | asm | remarks | flags | pgo | time | \
        profile) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|sanitize|asm|remarks|flags|pgo|time [filter]|profile]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs" "$ROOT/flags" "$WORK/"
cd "$WORK"
CC=${CC:-cc}
CSTD=${CSTD:-c17}
OPT=${OPT:--O2}
WARN='-Wall -Wextra -Werror -pedantic'
SRC='constructs/bench.c constructs/memory.c constructs/alloc.c
constructs/codegen.c constructs/io.c constructs/main.c'
"$CC" --version | head -n 1
IS_CLANG=
if "$CC" --version 2>/dev/null | grep -qi clang; then
    IS_CLANG=1
fi
# asm/remarks/flags/pgo use clang-only options or patterns recorded with
# clang; other compilers get an explicit NOT RUN instead of a false pass.
case "$MODE" in
    asm | remarks | flags | pgo)
        if [ -z "$IS_CLANG" ]; then
            echo "NOT RUN: $MODE requires clang (CC=$CC)"
            exit 0
        fi
        ;;
esac

# Machine-specific: the default macOS SDK can fail to link (a malformed
# libSystem.tbd). Keep the default when it links; otherwise use the first
# installed SDK that links a trivial program.
printf 'int main(void) { return 0; }\n' >probe.c
if ! "$CC" probe.c -o probe 2>/dev/null; then
    found=
    for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.*.sdk; do
        [ -d "$sdk" ] || continue
        if SDKROOT=$sdk "$CC" probe.c -o probe 2>/dev/null; then
            SDKROOT=$sdk
            export SDKROOT
            found=1
            break
        fi
    done
    [ -n "$found" ] || { echo 'no SDK links a trivial program' >&2; exit 1; }
fi
echo "SDKROOT=${SDKROOT:-default}"

build() { # build OUTPUT EXTRA_FLAGS...
    out=$1
    shift
    "$CC" -std="$CSTD" $OPT $WARN "$@" $SRC -o "$out"
}

# fn_asm FILE FUNCTION: one function's body from Mach-O or ELF assembly.
fn_asm() {
    awk -v a="_$2:" -v b="$2:" '
        $1 == a || $1 == b { on = 1 }
        on { print }
        on && /\.cfi_endproc/ { exit }
    ' "$1"
}

# expect FILE FUNCTION REGEX some|none
expect() {
    body=$(fn_asm "$1" "$2")
    [ -n "$body" ] || { echo "ASM $2: symbol not found" >&2; exit 1; }
    n=$(printf '%s\n' "$body" | grep -cE "$3" || true)
    echo "ASM $2: $n line(s) match /$3/"
    case "$4" in
        some) [ "$n" -gt 0 ] || { echo "expected /$3/ in $2" >&2; exit 1; } ;;
        none) [ "$n" -eq 0 ] || { echo "unexpected /$3/ in $2" >&2; exit 1; } ;;
    esac
}

case "$MODE" in
    verify)
        build ./cx
        ./cx verify
        saved=$CSTD
        CSTD=c23
        build ./cx23
        CSTD=$saved
        ./cx23 verify | grep -E 'CKD path|VERIFY'
        ref=$(./cx emit-write 50000 | cksum)
        for v in emit-batched emit-stdio emit-unbuffered; do
            got=$(./cx "$v" 50000 | cksum)
            [ "$got" = "$ref" ] || { echo "$v: output differs" >&2; exit 1; }
        done
        echo "EMIT identical output from all four variants ($ref)"
        ;;
    benchmark)
        build ./cx
        ./cx smoke
        ;;
    sanitize)
        OPT='-O1 -g -fno-omit-frame-pointer'
        build ./cx-san -fsanitize=address,undefined \
            -fno-sanitize-recover=all
        ./cx-san verify
        echo 'SANITIZE ASan+UBSan: verify passed with no report'
        "$CC" -std="$CSTD" -O1 -g -fsanitize=undefined \
            -fno-sanitize-recover=undefined flags/ub.c -o ub-san
        status=0
        ./ub-san >ub.out 2>&1 || status=$?
        if [ "$status" -eq 0 ] ||
            ! grep -q 'runtime error: signed integer overflow' ub.out; then
            cat ub.out
            echo 'UBSan did not report the signed overflow' >&2
            exit 1
        fi
        grep 'runtime error' ub.out
        echo "SANITIZE UBSan flagged ub.c (exit $status), as expected"
        ;;
    asm)
        "$CC" -std="$CSTD" $OPT -S constructs/codegen.c -o codegen.s
        "$CC" -std="$CSTD" $OPT -S constructs/memory.c -o memory.s
        "$CC" -std="$CSTD" $OPT -S flags/ub.c -o ub.s
        "$CC" -std="$CSTD" $OPT -c constructs/codegen.c -o codegen.o
        nm codegen.o | grep -q 'scale_extern' ||
            { echo 'extern helper missing from symbol table' >&2; exit 1; }
        if nm codegen.o | grep -q 'scale_static'; then
            echo 'static helper still emitted' >&2
            exit 1
        fi
        echo 'NM codegen.o: scale_extern emitted, scale_static not emitted'
        expect codegen.s apply_extern 'bl?[[:space:]]+_?scale_extern' none
        # Library idioms: the compiler turns these baseline loops into
        # calls, so the hand loop and the libc call are the same code.
        expect memory.s zero_loop '_?(bzero|memset)' some
        expect memory.s shift_loop '_?memmove' some
        expect codegen.s copy_restrict '_?memcpy' some
        expect codegen.s copy_plain '_?memcpy' none
        case $(uname -m) in
            arm64 | aarch64)
                p=$(fn_asm codegen.s bump_plain | grep -c 'ldr' || true)
                r=$(fn_asm codegen.s bump_restrict | grep -c 'ldr' || true)
                echo "ASM bump_plain: $p ldr, bump_restrict: $r ldr"
                [ "$r" -lt "$p" ] || { echo 'restrict saved no load' >&2; exit 1; }
                expect codegen.s lower_bound_branchy 'csel' some
                expect codegen.s lower_bound_branchless 'csel' some
                expect codegen.s clamp_branch 'smax' none
                expect codegen.s clamp_select 'smax' some
                expect codegen.s sum_f32_strict 'fadd\.4s' none
                expect codegen.s sum_f32_reassoc 'fadd\.4s' some
                expect codegen.s sum_f32_neon 'fadd\.4s' some
                expect codegen.s sum_checked_ckd 'b\.vs' some
                expect codegen.s sum_checked_precheck 'b\.vs' none
                expect ub.s next_wraps_ub 'mov[[:space:]]+w0, #0' some
                expect ub.s next_wraps_ub '[[:space:]](cmp|adds)[[:space:]]' none
                ;;
            *)
                echo "NOT ASSERTED on $(uname -m): register-level patterns"
                echo 'are written for aarch64 only.'
                ;;
        esac
        echo 'ASM PASSED'
        ;;
    remarks)
        "$CC" -std="$CSTD" $OPT -c constructs/codegen.c -o codegen.o \
            -fsave-optimization-record -foptimization-record-file=cg.yaml \
            -Rpass-missed=loop-vectorize 2>missed.txt
        grep 'remark' missed.txt | sed 's/^.*constructs\///' || true
        # One line per loop-vectorize record: kind function name width.
        awk '
            /^--- !/ { kind = $2; pass = ""; fn = ""; nm = ""; vf = "-" }
            /^Pass:/ { pass = $2 }
            /^Name:/ { nm = $2 }
            /^Function:/ { fn = $2 }
            /VectorizationFactor:/ { vf = $NF; gsub(/\047/, "", vf) }
            /^\.\.\./ { if (pass == "loop-vectorize") print kind, fn, nm, vf }
        ' cg.yaml | sort -u >records.txt
        cat records.txt
        need() {
            grep -q "^$1 $2 $3" records.txt ||
                { echo "missing record: $1 $2 $3" >&2; exit 1; }
        }
        need '!Passed' count_at_least_i32 'Vectorized 4'
        need '!Passed' count_at_least_u8 'Vectorized 16'
        need '!Passed' clamp_select Vectorized
        need '!Missed' upper_strlen_cond MissedDetails
        need '!Analysis' upper_strlen_cond UnsupportedUncountableLoop
        if grep -q '^!Analysis upper_hoisted UnsupportedUncountableLoop' \
            records.txt; then
            echo 'hoisted strlen loop is still uncountable' >&2
            exit 1
        fi
        echo 'REMARKS PASSED'
        ;;
    flags)
        for lto in none full thin; do
            case $lto in
                none) f='' ;;
                full) f='-flto' ;;
                thin) f='-flto=thin' ;;
            esac
                "$CC" -std="$CSTD" $OPT $WARN $f flags/lto_main.c \
                flags/lto_scale.c -o "lto-$lto"
            if command -v otool >/dev/null 2>&1; then
                n=$(otool -tv "lto-$lto" | grep -cE 'bl[[:space:]]+_lto_scale' || true)
            else
                n=$(objdump -d "lto-$lto" | grep -cE 'call.*<lto_scale>|bl.*<lto_scale>' || true)
            fi
            echo "LTO $lto: $n call site(s) to lto_scale; output $("./lto-$lto" 1000)"
            eval "calls_$lto=$n"
        done
        # shellcheck disable=SC2154 # assigned through eval above
        [ "$calls_none" -gt 0 ] && [ "$calls_full" -eq 0 ] &&
            [ "$calls_thin" -eq 0 ] ||
            { echo 'LTO did not inline the cross-TU call' >&2; exit 1; }
        if [ "$(uname -s)" = Darwin ]; then
            "$CC" -std="$CSTD" $WARN -O2 -dynamiclib flags/vis.c -o libvis.dylib
            "$CC" -std="$CSTD" $WARN -O2 -fvisibility=hidden -dynamiclib \
                flags/vis.c -o libvis-hidden.dylib
            d=$(nm -gU libvis.dylib | grep -c ' T ' || true)
            h=$(nm -gU libvis-hidden.dylib | grep -c ' T ' || true)
        else
            "$CC" -std="$CSTD" $WARN -O2 -fPIC -shared flags/vis.c -o libvis.so
            "$CC" -std="$CSTD" $WARN -O2 -fPIC -shared -fvisibility=hidden \
                flags/vis.c -o libvis-hidden.so
            d=$(nm -D --defined-only libvis.so | grep -c ' T vis_' || true)
            h=$(nm -D --defined-only libvis-hidden.so | grep -c ' T vis_' || true)
        fi
        echo "VISIBILITY exported functions: default $d, hidden $h"
        [ "$h" -lt "$d" ] || { echo 'hidden exported as many' >&2; exit 1; }
        for m in '' -mcpu=native -march=native; do
                cpu=$("$CC" $m -### -c probe.c 2>&1 |
                sed -n 's/.*"-target-cpu" "\([^"]*\)".*/\1/p')
            echo "TARGET-CPU ${m:-default}: ${cpu:-unknown}"
        done
        "$CC" -std="$CSTD" -O2 $WARN $SRC -o o2
        "$CC" -std="$CSTD" -O3 $WARN $SRC -o o3
        ./o3 verify >/dev/null
        echo "OPT-LEVEL binary bytes: -O2 $(wc -c <o2 | tr -d ' '), -O3 $(wc -c <o3 | tr -d ' '); -O3 passes verify"
        if "$CC" -target x86_64-apple-macos11 -std="$CSTD" -O2 $WARN -c \
            flags/dispatch.c -o dispatch-x86.o 2>/dev/null ||
            "$CC" -target x86_64-linux-gnu -std="$CSTD" -O2 $WARN -c \
                flags/dispatch.c -o dispatch-x86.o 2>/dev/null; then
            nm dispatch-x86.o | grep -E 'sum_avx2|sum_portable|cpu_model'
            echo 'DISPATCH x86-64 object compiled (not executed on this host)'
        else
            echo 'DISPATCH x86-64 cross-compile unavailable: not verified'
        fi
        "$CC" -std="$CSTD" -O2 $WARN flags/dispatch.c -o dispatch
        ./dispatch >/dev/null && echo "DISPATCH host build ran ($(uname -m))"
        echo 'FLAGS PASSED'
        ;;
    pgo)
        PD=$(xcrun --find llvm-profdata 2>/dev/null ||
            command -v llvm-profdata || true)
        [ -n "$PD" ] || { echo 'llvm-profdata not found: PGO not run'; exit 0; }
        echo "llvm-profdata: $PD"
        F="-std=$CSTD -O2 $WARN"
        "$CC" $F flags/pgo.c -o pgo-base
        # IR-based instrumentation (the manual's recommended PGO mode).
        "$CC" $F -fprofile-generate="$WORK/ir" flags/pgo.c -o pgo-irgen
        ./pgo-irgen 20 >/dev/null
        "$PD" merge -o ir.profdata "$WORK"/ir/*.profraw
        "$CC" $F -fprofile-use=ir.profdata -Werror=profile-instr-unprofiled \
            -Werror=profile-instr-out-of-date flags/pgo.c -o pgo-ir
        # Front-end instrumentation.
        "$CC" $F -fprofile-instr-generate flags/pgo.c -o pgo-fegen
        LLVM_PROFILE_FILE="$WORK/fe-%p.profraw" ./pgo-fegen 20 >/dev/null
        "$PD" merge -o fe.profdata "$WORK"/fe-*.profraw
        "$CC" $F -fprofile-instr-use=fe.profdata flags/pgo.c -o pgo-fe
        "$PD" show ir.profdata | head -n 3
        a=$(./pgo-base 20)
        [ "$a" = "$(./pgo-ir 20)" ] && [ "$a" = "$(./pgo-fe 20)" ] ||
            { echo 'PGO build changed the output' >&2; exit 1; }
        echo "PGO outputs identical ($a)"
        if command -v hyperfine >/dev/null 2>&1; then
            hyperfine -N --warmup 3 --runs 20 './pgo-base 300' \
                './pgo-ir 300' './pgo-fe 300'
        else
            echo 'hyperfine not installed: PGO not timed'
        fi
        ;;
    time)
        build ./cx
        ./cx time "${2:-}"
        if command -v hyperfine >/dev/null 2>&1; then
            hyperfine -N --warmup 3 --output=null \
                './cx emit-write 200000' \
                './cx emit-unbuffered 200000' \
                './cx emit-stdio 200000' \
                './cx emit-batched 200000'
        else
            echo 'hyperfine not installed: emit variants not timed'
        fi
        ;;
    profile)
        [ "$(uname -s)" = Darwin ] ||
            { echo 'profile mode uses macOS tools; use perf on Linux'; exit 0; }
        OPT='-O2 -g'
        build ./cx
        status=0
        leaks --atExit -- ./cx verify >leaks.out 2>&1 || status=$?
        grep -E 'leaks? for|Process [0-9]+:' leaks.out || true
        [ "$status" -eq 0 ] || { echo "leaks exit $status" >&2; exit 1; }
        echo 'LEAKS: 0 leaks reported for verify'
        ./cx hot 4 &
        pid=$!
        status=0
        sample "$pid" 2 -file sample.txt >/dev/null 2>&1 || status=$?
        wait "$pid"
        if [ "$status" -eq 0 ] && grep -q 'join_strcat' sample.txt; then
            grep -m 3 -E 'strcat|join_strcat' sample.txt
            echo 'SAMPLE: hot frame join_strcat found'
        else
            echo "SAMPLE unavailable (exit $status): not verified"
        fi
        status=0
        xctrace record --template 'Time Profiler' --time-limit 3s \
            --output tp.trace --launch -- ./cx hot 2 \
            >xctrace.out 2>&1 || status=$?
        if [ "$status" -eq 0 ]; then
            xctrace export --input tp.trace --toc >toc.xml 2>/dev/null &&
                grep -o 'schema="time-profile"' toc.xml | head -n 1
            echo 'XCTRACE: Time Profiler trace recorded'
        else
            grep -E 'Error|error' xctrace.out | head -n 3 || true
            echo "XCTRACE failed (exit $status): not verified"
        fi
        ;;
esac
