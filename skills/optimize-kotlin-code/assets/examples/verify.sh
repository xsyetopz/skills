#!/usr/bin/env sh
# Builds the Kotlin/JVM construct catalog with Maven in a disposable copy so
# the skill directory never receives target/, JMH results, or JFR files.
#
#   sh verify.sh verify [GROUP...]  equivalence + allocation oracles
#                                   (groups: inline representation
#                                   collections control coroutines)
#   sh verify.sh noea               same oracles with escape analysis off:
#                                   shows allocations C2 normally removes
#   sh verify.sh bytecode           javap assertions per construct
#   sh verify.sh benchmark          JMH smoke: every benchmark once, no timing
#   sh verify.sh measure            JMH with -prof gc; BENCH_FILTER selects;
#                                   the JSON result survives only when
#                                   BENCH_OUT names a directory
#   sh verify.sh jfr                JFR allocation profile of the oracles
#
# Needs JDK 17+, Maven 3.9, and network access on the first run (Kotlin
# 2.4.20, kotlinx.coroutines 1.11.0, JMH 1.37 go to ~/.m2). Set
# JMH_IGNORE_LOCK=1 only when another JMH run holds the lock and timing
# is not the point.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
[ "$#" -gt 0 ] && shift
case "$MODE" in
    verify | noea | bytecode | benchmark | measure | jfr) ;;
    *)
        echo 'usage: verify.sh [verify [GROUP...]|noea|bytecode|benchmark|measure|jfr]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs/." "$WORK/"
rm -rf "${WORK:?}/target"
cd "$WORK"
java -version 2>&1 | head -n 1
mvn -q -B package
JAR="$WORK/target/constructs.jar"
CLASSES="$WORK/target/classes"
JMH_LOCK=
[ "${JMH_IGNORE_LOCK:-0}" = 1 ] && JMH_LOCK=-Djmh.ignoreLock=true

# body CLASS METHOD: javap -c body of every overload named METHOD.
body() {
    javap -c -p -cp "$2" "$1" | awk -v m="$3" '
        /^  [^ ].*\(/ { on = index($0, " " m "(") > 0 }
        on { print }
        on && /^$/ { on = 0 }
    '
}

# expect CLASS METHOD REGEX some|none|N [CLASSPATH]
expect() {
    cp_=${5:-$CLASSES}
    text=$(body "$1" "$cp_" "$2")
    if [ -z "$text" ]; then
        echo "BYTECODE $1.$2: method not found" >&2
        exit 1
    fi
    n=$(printf '%s\n' "$text" | grep -cE "$3" || true)
    echo "BYTECODE $1.$2: $n line(s) match /$3/ (want $4)"
    case "$4" in
        some) [ "$n" -gt 0 ] || { echo "expected /$3/" >&2; exit 1; } ;;
        none) [ "$n" -eq 0 ] || { echo "unexpected /$3/" >&2; exit 1; } ;;
        *) [ "$n" -eq "$4" ] || { echo "expected $4 x /$3/" >&2; exit 1; } ;;
    esac
}

case "$MODE" in
    verify)
        # -Xbatch: compile synchronously so allocation deltas measure C2
        # code, not the interpreter.
        java -Xbatch -cp "$JAR" constructs.MainKt "$@"
        ;;
    noea)
        java -Xbatch -XX:-DoEscapeAnalysis -Dconstructs.reportOnly=1 \
            -cp "$JAR" constructs.MainKt \
            inline representation collections control
        ;;
    bytecode)
        I=constructs.InlineKt
        expect $I countAboveBaseline 'invokedynamic' 1
        expect $I countAboveCandidate 'invokedynamic|Function1' none
        expect $I countIfBaseline 'Integer.valueOf' some
        expect $I countIfBaseline 'Function1.invoke' some
        expect $I sumCapturedBaseline 'Ref.IntRef' some
        expect $I sumCapturedCandidate 'Ref.IntRef|invokedynamic' none
        expect $I countInstancesBaseline 'Class.isInstance' some
        expect $I stringsCandidate 'instanceof.*java/lang/String' some
        expect $I stringsCandidate 'isInstance' none
        expect $I useRegisterBaseline 'invokedynamic' 2
        expect $I useRegisterCandidate 'invokedynamic' 1
        expect $I useDeferBaseline 'invokedynamic' 1
        expect $I useDeferCandidate 'invokedynamic' none
        expect $I useDeferCandidate 'new .*inlined' some
        R=constructs.RepresentationKt
        expect $R totalBaseline 'new .*CentsBox' some
        expect $R totalCandidate 'new ' none
        expect $R pricesBaseline 'Cents."box-impl"' some
        expect $R squaresBaseline 'Integer.valueOf' some
        expect $R squaresArrayBaseline 'Integer.valueOf' some
        expect $R squaresCandidate 'Integer.valueOf' none
        expect $R maxOrNullBaseline 'Integer.intValue' some
        expect $R maxOrNullCandidate 'Integer.intValue' none
        expect $R bufferSizeBaseline 'getPLAIN_BUFFER_SIZE' some
        expect $R bufferSizeCandidate 'sipush +16384' some
        expect $R bufferSizeCandidate 'invokestatic' none
        expect $R readPropertyBaseline 'Point.getX' some
        expect $R readPropertyCandidate 'getfield .*Point.y' some
        # @JvmStatic does not change Kotlin call sites: still via Companion.
        expect $R readPropertyCandidate 'Point.Companion.originStatic' some
        expect $R statsBaseline 'Stats.copy' some
        expect $R statsCandidate 'Stats.copy' none
        C=constructs.ControlFlowKt
        for f in sumUntil sumRangeUntil sumIndices sumDownTo sumListIndices \
            sumEvenStepCandidate; do
            expect $C $f 'kotlin/ranges' none
        done
        expect $C sumEvenStepBaseline 'RangesKt.step' some
        expect $C sumForEachBaseline 'Iterable.iterator' some
        expect $C sumReversedBaseline 'RangesKt.reversed' some
        expect $C areaWhen 'instanceof' 3
        expect $C weightWhen 'tableswitch' some
        expect $C weightWhen 'WhenMappings' some
        expect $C methodWhen 'lookupswitch' some
        expect $C methodWhen 'String.hashCode' some
        L=constructs.CollectionsKt
        expect $L labelTemplate 'makeConcatWithConstants' some
        expect $L joinBaseline 'makeConcatWithConstants' some
        expect $L joinCandidate 'makeConcatWithConstants' none
        expect $L totalLengthBaseline 'Integer.valueOf' some
        expect $L totalLengthCandidate 'Integer.valueOf' none
        # Lazy implementations come from kotlin-stdlib inside the jar.
        expect kotlin.SynchronizedLazyImpl getValue 'monitorenter' some "$JAR"
        expect kotlin.SafePublicationLazyImpl getValue 'compareAndSet' some "$JAR"
        expect kotlin.UnsafeLazyImpl getValue 'monitorenter|compareAndSet' \
            none "$JAR"
        echo 'BYTECODE PASSED'
        ;;
    benchmark)
        # shellcheck disable=SC2086 # empty or one flag
        java $JMH_LOCK -jar "$JAR" -f 1 -wi 0 -i 1 -r 100ms -foe true \
            "${BENCH_FILTER:-.}"
        echo 'SMOKE PASSED: every benchmark ran once; not a timing result.'
        ;;
    measure)
        OUT=${BENCH_OUT:-$WORK/out}
        mkdir -p "$OUT"
        # shellcheck disable=SC2086 # empty or one flag
        java $JMH_LOCK -jar "$JAR" -prof gc -rf json \
            -rff "$OUT/jmh-result.json" "${BENCH_FILTER:-.}"
        if [ -n "${BENCH_OUT:-}" ]; then
            echo "Results: $OUT/jmh-result.json"
        else
            echo 'JSON discarded with the temporary copy; set BENCH_OUT to keep it.'
        fi
        ;;
    jfr)
        java -XX:StartFlightRecording=filename="$WORK/oracles.jfr",settings=profile \
            -cp "$JAR" constructs.MainKt collections >/dev/null
        jfr view allocation-by-class "$WORK/oracles.jfr"
        ;;
esac
