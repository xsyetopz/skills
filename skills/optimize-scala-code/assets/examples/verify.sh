#!/usr/bin/env sh
# shellcheck disable=SC2016 # JVM names such as apply$mcII$sp are literal.
# Runs the Scala construct catalog in a disposable copy so the skill
# directory never receives .scala-build/, .bsp/, class files, or JMH output.
#
#   sh verify.sh verify       equivalence + allocation oracles (default)
#   sh verify.sh diagnostics  javap bytecode assertions, Scala 2.13
#                             @specialized, expected compile failures
#   sh verify.sh benchmark    every JMH benchmark once: smoke, no timing
#   sh verify.sh measure      JMH with -prof gc and JSON results
#   sh verify.sh profile      JFR recording of a hot loop, then jfr views
#   sh verify.sh sbt          sbt 2 + sbt-jmh: every benchmark once (smoke)
#
# Environment: BENCH_FILTER (JMH regex, default .), BENCH_OUT (default
# ./bench-results), JMH_ARGS (extra JMH options for measure).
# Requires scala-cli 1.10+ and a JDK 17+ (developed on scala-cli 1.16.0,
# Scala 3.8.4, JDK 25). JMH needs the Bloop server: no --server=false.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | diagnostics | benchmark | measure | profile | sbt) ;;
    *)
        echo 'usage: verify.sh [verify|diagnostics|benchmark|measure|profile|sbt]' >&2
        exit 2
        ;;
esac
OUT=${BENCH_OUT:-$PWD/bench-results}
FILTER=${BENCH_FILTER:-.}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/constructs" "$ROOT/bench" "$ROOT/scala2" "$ROOT/negative" \
    "$ROOT/sbt" "$WORK/"
cd "$WORK"
# JMH takes a lock file in java.io.tmpdir; a private tmpdir keeps
# concurrent JMH runs on a shared machine from refusing to start.
mkdir -p "$WORK/tmp"
scala-cli version --cli-version
java -version 2>&1 | head -n 1

# expect NAME eq|ge N PATTERN FILE: assert that the number of lines of FILE
# matching the extended regex PATTERN is equal to (eq) or at least (ge) N.
expect() {
    got=$(grep -cE -- "$4" "$5" || true)
    if { [ "$2" = eq ] && [ "$got" -eq "$3" ]; } ||
        { [ "$2" = ge ] && [ "$got" -ge "$3" ]; }; then
        echo "PASS $1 ($got matching lines)"
    else
        echo "FAIL $1: $got lines match '$4', want $2 $3" >&2
        exit 1
    fi
}

# method CLASS NAME: print the javap -c body of method NAME in CLASS.
method() {
    javap -c -p -cp "$WORK/classes" "$1" |
        awk -v n=" $2(" 'index($0, n) && /^  [a-z]/ { p = 1 }
            p { print } p && /^$/ { exit }'
}

jmh() {
    scala-cli --power run --jmh constructs bench \
        --java-prop "java.io.tmpdir=$WORK/tmp" -- "$@"
}

case "$MODE" in
    verify)
        scala-cli run constructs --server=false --main-class constructs.verify
        ;;
    diagnostics)
        scala-cli compile constructs --server=false -d "$WORK/classes"
        C=constructs
        javap -s -p -cp "$WORK/classes" "$C.Units\$" "$C.ValueClassArray\$" \
            >"$WORK/sig.txt"
        expect 'opaque Array[Meters] is double[]' eq 2 \
            'descriptor: \(I\)\[D' "$WORK/sig.txt"
        expect 'value class array holds objects' eq 1 \
            'descriptor: \(I\)\[Lconstructs/MetersVC;' "$WORK/sig.txt"
        expect 'value class parameters erase to double' eq 1 \
            'descriptor: \(DD\)D' "$WORK/sig.txt"
        method "$C.FunctionSpecialization\$" baseline >"$WORK/fn.txt"
        method "$C.FunctionSpecialization\$" candidate >>"$WORK/fn.txt"
        expect 'Int => Int calls apply$mcII$sp' eq 1 \
            'Function1\.apply\$mcII\$sp:\(I\)I' "$WORK/fn.txt"
        expect 'generic Fn boxes the argument' eq 1 \
            'boxToInteger' "$WORK/fn.txt"
        method "$C.GenericBoxing\$" baseline >"$WORK/gb.txt"
        expect 'Numeric.plus takes Object' eq 1 \
            'Numeric\.plus:\(Ljava/lang/Object;Ljava/lang/Object;\)' \
            "$WORK/gb.txt"
        method "$C.GenericBoxing\$" inlinedLong >"$WORK/gbi.txt"
        expect 'inline def resolves plus to (JJ)J' eq 1 \
            'LongIsIntegral\$\.plus:\(JJ\)J' "$WORK/gbi.txt"
        method "$C.ArrayLoop\$" baseline >"$WORK/al.txt"
        expect 'Array.sum goes through Numeric' eq 1 \
            'ArraySeq\$ofInt\.sum:\(Lscala/math/Numeric;\)' "$WORK/al.txt"
        method "$C.Logging\$" baseline >"$WORK/log-value.txt"
        method "$C.Logging\$" byNameCall >"$WORK/log-name.txt"
        method "$C.Logging\$" candidate >"$WORK/log-inline.txt"
        expect 'by-value builds the message before the call' eq 1 \
            'makeConcatWithConstants' "$WORK/log-value.txt"
        expect 'by-name allocates a Function0' eq 1 \
            'apply:\(J\)Lscala/Function0;' "$WORK/log-name.txt"
        expect 'inline tests enabled before building' eq 1 \
            'ifeq' "$WORK/log-inline.txt"
        expect 'inline leaves no call to a log method' eq 0 \
            'Method by(Value|Name)' "$WORK/log-inline.txt"
        method "$C.TailRec\$" 'loop$1' >"$WORK/tr.txt"
        expect '@tailrec loop is a goto' ge 1 'goto' "$WORK/tr.txt"
        expect '@tailrec loop does not call itself' eq 0 \
            'Method loop\$1' "$WORK/tr.txt"
        method "$C.Switch\$" candidate >"$WORK/sw.txt"
        method "$C.Switch\$" baseline >"$WORK/if.txt"
        expect '@switch emits tableswitch' eq 1 'tableswitch' "$WORK/sw.txt"
        expect 'if chain has no switch' eq 0 'switch' "$WORK/if.txt"
        method "$C.SealedMatch\$" area >"$WORK/sealed.txt"
        expect 'sealed match is an instanceof chain' eq 3 'instanceof' \
            "$WORK/sealed.txt"
        javap -p -cp "$WORK/classes" "$C.Config" >"$WORK/lazy.txt"
        expect 'lazy val Int is a volatile Object field' eq 1 \
            'private volatile java\.lang\.Object factor\$lzy1;' \
            "$WORK/lazy.txt"
        expect '@threadUnsafe lazy val is a plain int field' eq 1 \
            'private int unsafeFactor\$lzy1;' "$WORK/lazy.txt"
        method "$C.Enrich\$" baseline >"$WORK/rich.txt"
        method "$C.Enrich\$" candidate >"$WORK/ext.txt"
        expect 'implicit class wraps the receiver' ge 1 \
            'Lconstructs/Enrich\$RichLong;' "$WORK/rich.txt"
        expect 'extension method takes the receiver as a long' eq 1 \
            'squaredPlusExt:\(JJ\)J' "$WORK/ext.txt"
        method "$C.ArrayAsSeq\$" sumSeq >"$WORK/seq.txt"
        method "$C.ArrayAsSeq\$" sumIArray >"$WORK/iarray.txt"
        expect 'Seq.apply returns a boxed element' eq 1 \
            'Seq\.apply:\(I\)Ljava/lang/Object;' "$WORK/seq.txt"
        expect 'IArray.apply returns int' eq 1 \
            'IArray\$\.apply:\(\[II\)I' "$WORK/iarray.txt"
        method "$C.Interpolation\$" plain >"$WORK/s.txt"
        method "$C.Interpolation\$" formattedPlain >"$WORK/f.txt"
        expect 's interpolator is invokedynamic concat' eq 1 \
            'makeConcatWithConstants' "$WORK/s.txt"
        expect 'f interpolator calls format' eq 1 'format\$extension' \
            "$WORK/f.txt"
        scala-cli compile scala2 --scala 2.13.18 --server=false \
            -d "$WORK/s2"
        scala-cli compile scala2 --scala 3.8.4 --server=false -d "$WORK/s3"
        ls "$WORK/s2/specialized" "$WORK/s3/specialized" >"$WORK/spec.txt"
        expect 'Scala 2.13 @specialized generates Box$mcI$sp' eq 1 \
            'Box\$mcI\$sp\.class' "$WORK/spec.txt"
        for f in TailrecNotTail SwitchNotSwitchable; do
            if scala-cli compile "negative/$f.scala" --server=false \
                >"$WORK/$f.txt" 2>&1; then
                echo "FAIL $f compiled; it must be rejected" >&2
                exit 1
            fi
        done
        expect 'non-tail @tailrec is rejected' ge 1 \
            'Cannot rewrite recursive call' "$WORK/TailrecNotTail.txt"
        expect 'Long @switch is rejected under -Werror' ge 1 \
            'Could not emit switch' "$WORK/SwitchNotSwitchable.txt"
        echo 'ALL DIAGNOSTICS PASSED'
        ;;
    benchmark)
        jmh -f 1 -wi 0 -i 1 -r 100ms "$FILTER"
        echo 'SMOKE PASSED: every benchmark ran once; not a timing result.'
        ;;
    measure)
        mkdir -p "$OUT"
        # shellcheck disable=SC2086 # JMH_ARGS is a list of options.
        jmh -prof gc -rf json -rff "$OUT/jmh.json" ${JMH_ARGS:-} "$FILTER" |
            tee "$OUT/jmh.txt"
        echo "Results: $OUT/jmh.json"
        ;;
    profile)
        mkdir -p "$OUT"
        scala-cli run constructs --server=false \
            --main-class constructs.profile \
            --java-opt "-XX:StartFlightRecording=filename=$OUT/profile.jfr" \
            -- 5
        jfr view hot-methods "$OUT/profile.jfr" | head -n 20
        jfr view allocation-by-class "$OUT/profile.jfr" | head -n 20
        echo "Recording: $OUT/profile.jfr"
        ;;
    sbt)
        # sbt 2 starts a background server; stop it before the temp
        # directory is removed. build.sbt passes JMH_TMPDIR to the forked
        # JMH runner as java.io.tmpdir (location of the JMH lock file).
        cd "$WORK/sbt"
        status=0
        JMH_TMPDIR="$WORK/tmp" sbt -batch \
            "Jmh/run -f 1 -wi 0 -i 1 -r 100ms $FILTER" || status=$?
        sbt shutdown >/dev/null 2>&1 || true
        [ "$status" -eq 0 ] || exit "$status"
        echo 'SMOKE PASSED: sbt-jmh ran every benchmark once; not a timing.'
        ;;
esac
