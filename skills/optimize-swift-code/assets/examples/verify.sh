#!/usr/bin/env sh
# Builds and runs the Swift construct catalog in a disposable copy so the
# skill directory never receives .build/ or benchmark output.
#
#   sh verify.sh verify     equivalence + malloc/retain/hash-count oracles
#   sh verify.sh benchmark  run every pair once (smoke; no timing)
#   sh verify.sh asm        assert dispatch, ARC, bounds, and overflow
#                           patterns in -emit-assembly output (arm64)
#   sh verify.sh wmo        SIL with and without whole-module optimization
#   sh verify.sh build      -O vs -Osize sizes, -O vs -Ounchecked traps
#   sh verify.sh time [F]   ContinuousClock medians for pairs matching F
#   sh verify.sh measure    package-benchmark (fetches pinned packages);
#                           BENCH_FILTER selects benchmarks by regex
#   sh verify.sh trace      xctrace Time Profiler recording (needs Xcode)
#
# Toolchain: every command goes through xcrun. On the machine these
# examples were recorded on, the swiftly-installed `swift build` failed at
# link time ("ld: tapi error: malformed file ... libSystem.B.tbd") and the
# swiftly `swiftc -typecheck` rejected "-target-arch-variant"; the same
# 6.3.3 toolchain selected through xcrun (TOOLCHAINS) worked.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | asm | wmo | build | time | measure | trace) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|asm|wmo|build|time [filter]|measure|trace]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs" "$ROOT/benchmarks" "$ROOT/wmo" "$ROOT/overflow" \
    "$WORK/"
rm -rf "$WORK/constructs/.build" "$WORK/benchmarks/.build"
C="$WORK/constructs"
S="$C/Sources"
xcrun swift --version 2>&1 | head -n 1

build() {
    xcrun swift build --package-path "$C" -c release "$@" >/dev/null
}
bin() {
    echo "$(xcrun swift build --package-path "$C" -c release \
        --show-bin-path)/Catalog"
}

# body FILE NAME: assembly of the function Constructs.NAME(...).
body() {
    awk -v n="$2" '
        BEGIN { pat = "^_\\$s10Constructs" length(n) n "[A-Za-z_].*:$" }
        !on && $1 ~ pat { on = 1 }
        on { print }
        on && /-- End function/ { exit }
    ' "$1"
}
# symbol FILE SYMBOL: assembly of one exact mangled symbol.
symbol() {
    awk -v s="$2:" '
        $1 == s { on = 1 }
        on { print }
        on && /-- End function/ { exit }
    ' "$1"
}
# loop: keep only basic blocks LLVM annotated as loop members.
loop() {
    awk '
        /^L[A-Za-z0-9_]*:/ { in_loop = ($0 ~ /Loop Header|in Loop:/) }
        in_loop { print }
    '
}
# expect FILE NAME REGEX some|none [loop]
expect() {
    text=$(body "$1" "$2")
    if [ -z "$text" ]; then
        echo "ASM $2: symbol not found in $1" >&2
        exit 1
    fi
    scope=function
    if [ "${5:-}" = loop ]; then
        text=$(printf '%s\n' "$text" | loop)
        scope=loop
    fi
    n=$(printf '%s\n' "$text" | grep -cE "$3" || true)
    echo "ASM $(basename "$1") $2 ($scope): $n line(s) match /$3/"
    case "$4" in
        some) [ "$n" -gt 0 ] || { echo "expected /$3/ in $2" >&2; exit 1; } ;;
        none) [ "$n" -eq 0 ] || { echo "unexpected /$3/ in $2" >&2; exit 1; } ;;
    esac
}

case "$MODE" in
    verify)
        build
        "$(bin)" verify
        ;;
    benchmark)
        build
        "$(bin)" smoke
        ;;
    time)
        build
        "$(bin)" time "${2:-}"
        ;;
    asm)
        A="$WORK/asm"
        mkdir -p "$A/cmo" "$A/evo"
        # Helper twice: default (conservative cross-module optimization
        # serializes small bodies) and with library evolution (resilient:
        # only @inlinable bodies cross the module boundary).
        xcrun swiftc -O -wmo -parse-as-library -module-name Helper \
            -emit-module -emit-module-path "$A/cmo/Helper.swiftmodule" \
            "$S/Helper/Helper.swift"
        xcrun swiftc -O -wmo -parse-as-library -enable-library-evolution \
            -module-name Helper -emit-module \
            -emit-module-path "$A/evo/Helper.swiftmodule" \
            "$S/Helper/Helper.swift"
        emit() { # emit OUT HELPERDIR FLAGS...
            out=$1
            dir=$2
            shift 2
            xcrun swiftc -wmo -parse-as-library -module-name Constructs \
                -I "$dir" "$@" -emit-assembly "$S"/Constructs/*.swift \
                -o "$out"
        }
        emit "$A/o.s" "$A/cmo" -O
        emit "$A/evo.s" "$A/evo" -O
        emit "$A/noexcl.s" "$A/cmo" -O -enforce-exclusivity=unchecked
        emit "$A/unchecked.s" "$A/cmo" -Ounchecked
        xcrun swiftc -O -wmo -parse-as-library -module-name Constructs \
            -I "$A/cmo" -emit-sil "$S"/Constructs/*.swift -o "$A/o.sil"
        # sil_count NAME: class_method lines in one SIL function body.
        sil_count() {
            awk -v n="$1" '
                $1 == "sil" && index($0, "@$s10Constructs" length(n) n) {
                    on = 1
                }
                on { print }
                on && /^} \/\/ end sil function/ { exit }
            ' "$A/o.sil" | grep -c 'class_method' || true
        }
        open_vt=$(sil_count totalAreaOpen)
        final_vt=$(sil_count totalAreaFinal)
        echo "SIL totalAreaOpen: class_method=$open_vt;" \
            "totalAreaFinal: class_method=$final_vt"
        if [ "$open_vt" -eq 0 ] || [ "$final_vt" -ne 0 ]; then
            echo 'expected class_method only in totalAreaOpen' >&2
            exit 1
        fi
        O="$A/o.s"
        case $(uname -m) in
            arm64 | aarch64) ;;
            *)
                echo "NOT ASSERTED on $(uname -m): patterns are arm64."
                exit 0
                ;;
        esac
        # Dispatch.
        expect "$O" totalAreaOpen 'blr' some
        expect "$O" totalAreaFinal 'blr' none
        expect "$O" tallyInternal 'blr' none
        expect "$O" countLegacy 'objc_msgSend' some
        expect "$O" countSwift 'objc_msgSend' none
        expect "$O" totalMixedAny 'blr' some
        expect "$O" totalMixedEnum 'blr' none
        text=$(symbol "$O" "_\$s10Constructs9ScoredAnyV5totalySiSaySiGF")
        n=$(printf '%s\n' "$text" | grep -c 'blr' || true)
        echo "ASM o.s ScoredAny.total (function): $n line(s) match /blr/"
        [ "$n" -gt 0 ] || { echo 'expected blr in ScoredAny.total' >&2; exit 1; }
        expect "$O" pipelineGeneric 'blr' none
        expect "$O" pipelineGeneric 'Tg5' some
        # No difference: with a concrete argument visible, -O specializes
        # the `any` parameter too; callAny and callSome end up identical
        # (merged) and neither makes an indirect call.
        expect "$O" callAny 'blr' none
        expect "$O" callSome 'blr' none
        # Cross-module calls.
        expect "$A/evo.s" scaleAllOpaque 'Helper11helperScale' some
        expect "$A/evo.s" scaleAllInlinable 'Helper[0-9]+helperScale' none
        expect "$A/evo.s" scaleAllMeters 'Helper5Meter' none
        expect "$O" scaleAllOpaque 'Helper11helperScale' none
        # ARC and storage.
        expect "$O" sumList '_swift_retain' some
        expect "$O" sumListValues '_swift_retain' none
        expect "$O" totalMass '_CocoaArrayWrapper|getElementSlowPath' some
        expect "$O" totalMassContiguous '_CocoaArrayWrapper|getElementSlowPath' none
        expect "$O" countWithEscapingCapture '_swift_allocObject' some
        expect "$O" countWithInout '_swift_allocObject' none
        # Bounds checks: a data-dependent index keeps one compare-and-trap
        # per iteration; a monotonic loop does not (hoisted by -O).
        B='b\.(ls|hs|lo|hi)'
        expect "$O" tallyChecked "$B" some loop
        expect "$O" tallyUnsafe "$B" none loop
        expect "$O" sumPrefixIndexed "$B|brk" none loop
        expect "$O" sumArray "$B|brk" none loop
        expect "$O" sumSpan "$B|brk" none loop
        # Overflow checks and vectorization.
        expect "$O" sumChecked 'b\.vs' some
        expect "$O" sumWrapping 'b\.vs' none
        expect "$A/unchecked.s" sumChecked 'b\.vs|brk' none
        # Exclusivity: -O widened the access to the whole loop.
        expect "$O" accumulateProperty '_swift_beginAccess' some
        expect "$O" accumulateProperty '_swift_beginAccess' none loop
        expect "$A/noexcl.s" accumulateProperty '_swift_beginAccess' none
        expect "$A/noexcl.s" countWithEscapingCapture '_swift_beginAccess' none
        for f in wordsShifting wordsRawSpan; do
            n=$(body "$O" "$f" | grep -c 'brk' || true)
            echo "ASM o.s $f: $n trap site(s) (recorded, not asserted)"
        done
        echo 'ASM PASSED'
        ;;
    wmo)
        D="$WORK/wmo"
        SDK=$(xcrun --show-sdk-path)
        # Without WMO the frontend compiles Use.swift alone (Counter.swift
        # is only parsed): no final inference, no cross-file specialization.
        xcrun swiftc -frontend -emit-sil -O -parse-as-library \
            -module-name WMODemo -sdk "$SDK" -primary-file "$D/Use.swift" \
            "$D/Counter.swift" -o "$D/file.sil"
        xcrun swiftc -O -wmo -parse-as-library -module-name WMODemo \
            -emit-sil "$D/Use.swift" "$D/Counter.swift" -o "$D/wmo.sil"
        for f in file wmo; do
            vt=$(grep -c 'class_method' "$D/$f.sil" || true)
            gen=$(grep -cE "function_ref @\\\$s7WMODemo9sumMapped" \
                "$D/$f.sil" || true)
            echo "SIL $f: class_method=$vt unspecialized_generic_refs=$gen"
            eval "vt_$f=$vt gen_$f=$gen"
        done
        # shellcheck disable=SC2154 # assigned through eval above
        if [ "$vt_file" -gt 0 ] && [ "$vt_wmo" -eq 0 ] &&
            [ "$gen_file" -gt 0 ] && [ "$gen_wmo" -eq 0 ]; then
            echo 'WMO PASSED'
        else
            echo 'WMO FAILED: expected dispatch and generic calls to vanish' >&2
            exit 1
        fi
        ;;
    build)
        size_of() {
            xcrun size -m "$1" | awk '/^Segment __TEXT:/ { print $3 }'
        }
        build
        o=$(size_of "$(bin)")
        build -Xswiftc -Osize
        s=$(size_of "$(bin)")
        "$(bin)" verify >/dev/null
        echo "SIZE Catalog __TEXT: -O $o bytes, -Osize $s bytes"
        echo 'The -Osize build still passes verify.'
        V="$WORK/overflow"
        xcrun swiftc -O "$V/Overflow.swift" -o "$V/checked"
        xcrun swiftc -Ounchecked "$V/Overflow.swift" -o "$V/unchecked"
        status=0
        "$V/checked" overflow >/dev/null 2>&1 || status=$?
        echo "OVERFLOW -O: exit status $status (trap expected: 133)"
        [ "$status" -eq 133 ] || { echo 'no overflow trap under -O' >&2; exit 1; }
        status=0
        "$V/unchecked" overflow >/dev/null 2>&1 || status=$?
        echo "OVERFLOW -Ounchecked: exit status $status (no trap; the"
        echo 'printed value is undefined and is deliberately not checked)'
        ;;
    measure)
        P="$WORK/benchmarks"
        xcrun swift package --package-path "$P" resolve \
            --only-use-versions-from-resolved-file >/dev/null
        xcrun swift package --package-path "$P" benchmark --no-progress \
            ${BENCH_FILTER:+--filter "$BENCH_FILTER"}
        ;;
    trace)
        if ! xcrun --find xctrace >/dev/null 2>&1; then
            echo 'NOT RUN: xctrace needs a full Xcode installation.'
            exit 0
        fi
        build
        T="$WORK/time.trace"
        xcrun xctrace record --quiet --template 'Time Profiler' \
            --output "$T" --launch -- "$(bin)" time offset >/dev/null
        xcrun xctrace export --input "$T" --xpath \
            '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' \
            >"$WORK/profile.xml"
        n=$(grep -c 'charactersByOffset' "$WORK/profile.xml" || true)
        echo "TRACE time-profile rows naming charactersByOffset: $n"
        [ "$n" -gt 0 ] || { echo 'profile has no catalog frames' >&2; exit 1; }
        # Allocations must attach to the process: without the
        # get-task-allow entitlement the recording reported "Failed to
        # attach to target process". Sign a copy for profiling only.
        cp "$(bin)" "$WORK/Catalog"
        cat >"$WORK/ent.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>com.apple.security.get-task-allow</key><true/>
</dict></plist>
PLIST
        codesign -f -s - --entitlements "$WORK/ent.plist" "$WORK/Catalog" \
            2>/dev/null
        A="$WORK/alloc.trace"
        xcrun xctrace record --quiet --template 'Allocations' \
            --time-limit 60s --output "$A" --launch -- "$WORK/Catalog" \
            time lazy >/dev/null
        xcrun xctrace export --input "$A" --xpath \
            '/trace-toc/run[@number="1"]/tracks/track[@name="Allocations"]/details/detail[@name="Statistics"]' \
            >"$WORK/alloc.xml"
        row=$(grep 'category="All Heap Allocations"' "$WORK/alloc.xml" || true)
        [ -n "$row" ] || { echo 'no Allocations statistics' >&2; exit 1; }
        echo "TRACE Allocations: $(printf '%s\n' "$row" |
            grep -oE 'count-total="[0-9]+"|total-bytes="[0-9]+"' |
            tr '\n' ' ')"
        echo 'TRACE PASSED'
        ;;
esac
