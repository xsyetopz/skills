#!/usr/bin/env sh
# Builds and runs the Java construct catalog in a disposable copy so the
# skill directory never receives target/, native libraries, or recordings.
#
#   sh verify.sh verify     equivalence oracles and deterministic claims
#   sh verify.sh benchmark  JMH smoke: every benchmark runs once, no timing
#   sh verify.sh measure    JMH with -prof gc, JSON export, alloc assertions
#   sh verify.sh tools      GC logs, JFR, jcmd, JIT logs, pinning events
#   sh verify.sh startup    AppCDS and AOT cache creation, use, and timing
#
# Requires JDK 25 (java, javac, jfr, jcmd), Maven 3.9, cc, and python3.
# Optional: hyperfine (startup timing). Environment: BENCH_FILTER (regex),
# BENCH_OUT (result directory), FORKS (JMH forks, default 1), JMH_ARGS
# (extra JMH options, not -f), CC (C compiler for the JNI/FFM library),
# RUNS (hyperfine runs).
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../.." && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | benchmark | measure | tools | startup) ;;
    *)
        echo 'usage: verify.sh [verify|benchmark|measure|tools|startup]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
BG=''
cleanup() {
    if [ -n "$BG" ]; then kill "$BG" 2>/dev/null || true; fi
    rm -rf "$WORK"
}
trap cleanup 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/jmh/." "$WORK/"
rm -rf "${WORK:?}/target"
cd "$WORK"

java -version 2>&1 | head -n 1
JAVA_HOME_DIR=$(java -XshowSettings:properties -version 2>&1 |
    awk -F' = ' '/java.home/ {print $2}')
case "$(uname -s)" in
    Darwin) LIB="$WORK/libnativeadd.dylib" OSINC=darwin ;;
    *) LIB="$WORK/libnativeadd.so" OSINC=linux ;;
esac
build_lib() {
    "${CC:-cc}" -shared -fPIC -O2 -I"$JAVA_HOME_DIR/include" \
        -I"$JAVA_HOME_DIR/include/$OSINC" -o "$LIB" src/main/c/native_add.c
}
if ! build_lib 2>"$WORK/cc.log"; then
    # Some macOS SDKs fail to link (ld: tapi error); retry installed SDKs.
    built=
    for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.*.sdk; do
        [ -d "$sdk" ] || continue
        if SDKROOT=$sdk build_lib 2>>"$WORK/cc.log"; then
            echo "NOTE linked with SDKROOT=$sdk"
            built=1
            break
        fi
    done
    [ -n "$built" ] || { cat "$WORK/cc.log" >&2; exit 1; }
fi
mvn -q -B package
JAR="$WORK/target/benchmarks.jar"
JOPTS="--add-opens java.base/java.util=ALL-UNNAMED \
--add-modules jdk.incubator.vector --enable-native-access=ALL-UNNAMED \
-Dnative.lib=$LIB"
# -jvmArgs (not -jvmArgsAppend) keeps each @Fork(jvmArgsAppend=...) intact.
# JMH takes a lock file in java.io.tmpdir; a private tmpdir lets this run
# coexist with other JMH runs on a shared machine (timings still interact).
FORK_ARGS="-Dnative.lib=$LIB --enable-native-access=ALL-UNNAMED"

# Prints count, total, and max of the "Pause ... N.NNNms" lines of a GC log.
pauses() {
    awk '/Pause/ && $NF ~ /ms$/ { v = $NF; sub(/ms$/, "", v);
        n++; t += v; if (v > m) m = v }
        END { printf "pauses=%d total=%.1fms max=%.3fms\n", n, t, m }' "$1"
}

need() {
    grep -q "$2" "$1" || {
        echo "FAIL: '$2' not found in $1" >&2
        exit 1
    }
}

case "$MODE" in
    verify)
        # shellcheck disable=SC2086
        java $JOPTS -cp "$JAR" example.Verify
        ;;
    benchmark)
        java -Djava.io.tmpdir="$WORK" -jar "$JAR" "${BENCH_FILTER:-.*}" \
            -f 1 -wi 0 -i 1 -r 100ms -jvmArgs "$FORK_ARGS" -foe true -rf json \
            -rff "$WORK/smoke.json" >"$WORK/smoke.txt"
        python3 "$SKILL/scripts/jmh_compare.py" "$WORK/smoke.json"
        echo 'SMOKE PASSED: every benchmark ran once; not a timing result.'
        ;;
    measure)
        OUT=${BENCH_OUT:-$PWD/bench-results}
        mkdir -p "$OUT"
        echo "JMH log: $OUT/jmh.txt"
        # shellcheck disable=SC2086
        java -Djava.io.tmpdir="$WORK" -jar "$JAR" "${BENCH_FILTER:-.*}" \
            -f "${FORKS:-1}" -wi 3 -i 5 -w 1s -r 1s -prof gc \
            -jvmArgs "$FORK_ARGS" -foe true -rf json -rff "$OUT/jmh.json" \
            ${JMH_ARGS:-} >"$OUT/jmh.txt" 2>&1
        grep '^# VM options:' "$OUT/jmh.txt" | sort | uniq -c
        if [ -n "${BENCH_FILTER:-}" ]; then
            python3 "$SKILL/scripts/jmh_compare.py" "$OUT/jmh.json"
        else
            python3 "$SKILL/scripts/jmh_compare.py" "$OUT/jmh.json" \
                --margin 0.05 \
                --alloc-lower escapeLocalNoEA:escapeLocal \
                --alloc-lower escapeEscaping:escapeLocal \
                --alloc-lower stringLoopConcat:stringLoopBuilder \
                --alloc-same stringExprBuilder:stringExprConcat \
                --alloc-lower listDefault:listPresized \
                --alloc-lower mapDefault:mapNewHashMap \
                --alloc-lower mapCapacityArg:mapNewHashMap \
                --alloc-lower keyLookupString:keyLookupRecord \
                --alloc-lower squaresStream:squaresLoop \
                --alloc-lower objectDefault:objectCompact \
                --alloc-lower twoIntsDefault:twoIntsCompact
        fi
        echo "Results: $OUT/jmh.json"
        ;;
    tools)
        echo '== GC logs (-Xlog:gc,gc+phases)'
        for gc in G1 Z Parallel; do
            case "$gc" in
                G1) flag='-XX:+UseG1GC' banner='Using G1' ;;
                Z) flag='-XX:+UseZGC' banner='Using The Z Garbage Collector' ;;
                *) flag='-XX:+UseParallelGC' banner='Using Parallel' ;;
            esac
            java "$flag" -Xmx256m -Xlog:gc,gc+phases:file="gc-$gc.log" \
                -cp "$JAR" example.Workload gc 3
            need "gc-$gc.log" "$banner"
            printf '%s: ' "$gc"
            pauses "gc-$gc.log"
        done
        java -XX:ActiveProcessorCount=1 -Xlog:gc -version 2>&1 | head -n 1
        echo '== JFR (-XX:StartFlightRecording, jfr summary/print/view)'
        java -XX:StartFlightRecording=filename=rec.jfr,settings=profile \
            -cp "$JAR" example.Workload gc 3 >/dev/null
        jfr summary rec.jfr >summary.txt
        need summary.txt 'jdk.ExecutionSample'
        grep -E ' jdk\.(ExecutionSample|ObjectAllocationSample|GCPhasePause) ' \
            summary.txt
        jfr view --width 100 hot-methods rec.jfr | head -n 8
        jfr view --width 100 allocation-by-class rec.jfr | head -n 7
        jfr print --events jdk.ObjectAllocationSample --stack-depth 2 \
            rec.jfr | head -n 12
        echo '== jcmd against a running JVM'
        java -cp "$JAR" example.Workload wait 30 &
        BG=$!
        sleep 2
        jcmd "$BG" VM.version
        jcmd "$BG" GC.class_histogram | head -n 6
        jcmd "$BG" JFR.start name=live settings=profile >/dev/null
        jcmd "$BG" JFR.dump name=live filename="$WORK/live.jfr" >/dev/null
        jfr summary live.jfr | head -n 4
        kill "$BG"
        wait "$BG" 2>/dev/null || true
        BG=''
        echo '== JIT (-XX:+PrintCompilation, PrintInlining)'
        java -XX:+PrintCompilation -cp "$JAR" example.Workload jit \
            >comp.txt
        need comp.txt 'Escape::local'
        grep 'Escape::local' comp.txt | head -n 4
        java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining \
            -cp "$JAR" example.Workload jit >inl.txt
        need inl.txt 'lengthSquared (24 bytes)   inline (hot)'
        grep 'lengthSquared' inl.txt | sort | uniq -c
        echo '== Virtual thread pinning (jdk.VirtualThreadPinned)'
        java -XX:StartFlightRecording=filename=pin.jfr -cp "$JAR" \
            example.Workload pinning >/dev/null 2>&1
        jfr print --events jdk.VirtualThreadPinned pin.jfr >pin.txt
        need pin.txt 'SlowInit.<clinit>'
        n=$(grep -c 'jdk.VirtualThreadPinned' pin.txt)
        echo "pinned events=$n (expected 1: class init; synchronized: none)"
        [ "$n" -eq 1 ] || exit 1
        echo 'TOOLS PASSED'
        ;;
    startup)
        run() { java "$@" -cp "$JAR" example.Workload startup; }
        run -XX:ArchiveClassesAtExit=app.jsa >/dev/null 2>&1
        run -XX:AOTCacheOutput=app.aot >/dev/null 2>&1
        for opt in -Xshare:off -Xshare:auto -XX:SharedArchiveFile=app.jsa \
            -XX:AOTCache=app.aot; do
            run "$opt" -Xlog:class+load >cl.txt
            printf '%s classes=%s shared=%s\n' "$opt" \
                "$(grep -c 'class,load' cl.txt)" \
                "$(grep -c 'shared objects file' cl.txt)"
        done
        run -XX:AOTCache=app.aot -XX:AOTMode=on >/dev/null
        run -XX:SharedArchiveFile=app.jsa -Xlog:class+load >cl.txt
        need cl.txt 'example.Workload source: shared objects file (top)'
        if command -v hyperfine >/dev/null; then
            hyperfine -N --warmup 3 --runs "${RUNS:-20}" \
                "java -Xshare:off -cp $JAR example.Workload startup" \
                "java -cp $JAR example.Workload startup" \
                "java -XX:SharedArchiveFile=app.jsa -cp $JAR \
example.Workload startup" \
                "java -XX:AOTCache=app.aot -cp $JAR example.Workload startup"
        else
            echo 'SKIP timing: hyperfine not installed'
        fi
        echo 'STARTUP PASSED'
        ;;
esac
