#!/usr/bin/env sh
# Verifies the Eclipse example plug-in in disposable copies, so target/,
# bin/, and workspaces never land in the skill directory.
#
#   sh verify.sh [offline]  bundle checker and its tests, XML parsing,
#                           pure logic executed on a plain JVM, manifest
#                           parser behavior, and every plug-in and test
#                           source compiled against Eclipse jars from the
#                           Tycho p2 cache (SKIP when the cache is empty)
#   sh verify.sh network    Tycho 5.0.4 build with UI-harness tests (a
#                           workbench window opens), JAR and p2 repository
#                           inspection, three negative builds (missing
#                           final newline, cut bin.includes, no
#                           singleton), and a p2 director install of the
#                           platform plus the feature into a temp folder
#
# network needs Maven 3.9.9+, Java 21+, a desktop session (or Xvfb on
# Linux), and download.eclipse.org. PYTHON, JAVA, JAVAC, MVN override
# tools; P2_CACHE overrides ~/.m2/repository/p2/osgi/bundle.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../.." && pwd)
MODE=${1:-offline}
case "$MODE" in
    offline | network) ;;
    *)
        echo 'usage: verify.sh [offline|network]' >&2
        exit 2
        ;;
esac
PY=${PYTHON:-python3}
JAVA=${JAVA:-java}
JAVAC=${JAVAC:-javac}
MVN=${MVN:-mvn}
P2_CACHE=${P2_CACHE:-$HOME/.m2/repository/p2/osgi/bundle}
PYTHONDONTWRITEBYTECODE=1
export PYTHONDONTWRITEBYTECODE
WORK=$(mktemp -d "${TMPDIR:-/tmp}/eclipse-verify.XXXXXX")
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

fresh_copy() {
    rm -rf "${WORK:?}/${1:?}"
    cp -R "$ROOT/plugin" "$WORK/$1"
    find "$WORK/$1" \( -name target -o -name bin \) -type d -prune \
        -exec rm -rf {} +
}

offline() {
    "$PY" "$SKILL/scripts/test_check_bundle.py" >"$WORK/checker.log" 2>&1 ||
        fail "checker tests: $(tail -n 20 "$WORK/checker.log")"
    ok "check_bundle.py tests: $(grep '^Ran' "$WORK/checker.log")"
    "$PY" "$SKILL/scripts/check_bundle.py" "$ROOT/plugin/org.acme.todos" \
        "$ROOT/plugin/org.acme.todos.tests" >"$WORK/check.log" ||
        fail "check_bundle.py: $(cat "$WORK/check.log")"
    ok "check_bundle.py on both bundles: $(tail -n 1 "$WORK/check.log")"

    find "$ROOT/plugin" \( -name '*.xml' -o -name '*.target' \) \
        -type f >"$WORK/xml.txt"
    "$PY" -c 'import sys, xml.etree.ElementTree as ET
for line in open(sys.argv[1]):
    ET.parse(line.strip())' "$WORK/xml.txt" || fail "XML parse"
    ok "$(wc -l <"$WORK/xml.txt" | tr -d ' ') XML files parse"

    mkdir -p "$WORK/logic"
    "$JAVAC" -Xlint:all -Werror -d "$WORK/logic" \
        "$ROOT/plugin/org.acme.todos/src/org/acme/todos/TodoScanner.java"
    "$JAVA" -cp "$WORK/logic" "$ROOT/logic/TodoScannerCheck.java" \
        >"$WORK/logic.log" || fail "logic: $(cat "$WORK/logic.log")"
    ok "TodoScanner on a plain JVM: $(grep -c '^ok' "$WORK/logic.log") checks"
    "$JAVA" "$ROOT/logic/ManifestNewlineCheck.java" >"$WORK/mf.log"
    grep -q 'Bundle-SymbolicName = null' "$WORK/mf.log" ||
        fail "manifest check: $(cat "$WORK/mf.log")"
    ok "java.util.jar.Manifest drops a header without a final newline"

    if [ ! -d "$P2_CACHE/org.eclipse.ui.workbench" ]; then
        echo "SKIP compile against Eclipse jars: no p2 cache at $P2_CACHE"
        return
    fi
    # Newest cached version of every bundle, sources excluded.
    : >"$WORK/cp.txt"
    for dir in "$P2_CACHE"/*/; do
        case "$dir" in *.source/) continue ;; esac
        newest=$(find "$dir" -name '*.jar' ! -name '*-sources.jar' |
            sort | tail -n 1)
        [ -n "$newest" ] && printf '%s:' "$newest" >>"$WORK/cp.txt"
    done
    classpath=$(cat "$WORK/cp.txt")
    mkdir -p "$WORK/classes"
    find "$ROOT/plugin" -name '*.java' >"$WORK/sources.txt"
    "$JAVAC" --release 21 -proc:none -d "$WORK/classes" -cp "$classpath" \
        @"$WORK/sources.txt" >"$WORK/javac.log" 2>&1 ||
        fail "javac against p2 cache: $(tail -n 30 "$WORK/javac.log")"
    ok "COMPILED $(wc -l <"$WORK/sources.txt" | tr -d ' ') sources against \
$P2_CACHE (not executed)"
}

# mvn_in DIR LOG ARGS... : Maven in a copy; the log stays in WORK.
mvn_in() {
    dir=$1
    log=$2
    shift 2
    (cd "$WORK/$dir" && "$MVN" -B "$@") >"$WORK/$log" 2>&1
}

network() {
    command -v "$MVN" >/dev/null || fail "no Maven ($MVN)"
    "$MVN" -v | head -n 3
    fresh_copy build
    mvn_in build build.log clean verify ||
        fail "mvn verify: $(grep -E 'ERROR|FAIL' "$WORK/build.log" | head -20)"
    summary=$(grep -E '^Tests run: [0-9]+, Failures' "$WORK/build.log" |
        tail -n 1)
    [ "$summary" = 'Tests run: 26, Failures: 0, Errors: 0, Skipped: 0' ] ||
        fail "unexpected test summary: $summary"
    ok "tycho-surefire plugin-test (UI harness): $summary"
    grep -E 'per POST_CHANGE|per event|cancelled scan|disposed with owner|rule violation|iterations before|listener write|late update|worker access' \
        "$WORK/build.log" | sed 's/^/     /'

    jar="$WORK/build/org.acme.todos/target/org.acme.todos-1.0.0-SNAPSHOT.jar"
    unzip -l "$jar" >"$WORK/jar.txt"
    grep -q ' plugin.xml$' "$WORK/jar.txt" || fail "plugin.xml not in JAR"
    grep -q 'org/acme/todos/ScanTodosJob.class' "$WORK/jar.txt" ||
        fail "classes not in JAR"
    ok "bundle JAR has plugin.xml and $(grep -c '\.class$' "$WORK/jar.txt") \
classes"
    unzip -p "$jar" META-INF/MANIFEST.MF >"$WORK/packaged.mf"
    grep -q 'Require-Capability: osgi.ee' "$WORK/packaged.mf" ||
        fail "no osgi.ee requirement in packaged manifest"
    if grep -q 'Bundle-RequiredExecutionEnvironment' "$WORK/packaged.mf"; then
        fail "packaged manifest still has Bundle-RequiredExecutionEnvironment"
    fi
    ok "Tycho replaced Bundle-RequiredExecutionEnvironment with osgi.ee"
    repo="$WORK/build/org.acme.todos.repository/target/repository"
    ls "$repo"/plugins/org.acme.todos_*.jar \
        "$repo"/features/org.acme.todos.feature_*.jar >/dev/null ||
        fail "p2 repository lacks the bundle or feature"
    ok "p2 repository: $(cd "$repo" && find . -type f | sort | tr '\n' ' ')"

    fresh_copy nonl
    mf="$WORK/nonl/org.acme.todos/META-INF/MANIFEST.MF"
    printf '%s' "$(cat "$mf")" >"$mf.tmp" && mv "$mf.tmp" "$mf"
    mvn_in nonl nonl.log package -pl org.acme.todos ||
        fail "no-newline build: $(tail -n 20 "$WORK/nonl.log")"
    if unzip -p "$WORK/nonl/org.acme.todos/target/"*.jar \
        META-INF/MANIFEST.MF | grep -q Automatic-Module-Name; then
        fail "last header survived a missing final newline"
    fi
    ok "missing final newline: build passes, Automatic-Module-Name dropped"

    fresh_copy cut
    printf 'source.. = src/\noutput.. = bin/\nbin.includes = META-INF/,\n%s\n%s\n' \
        '               .,' '               plugin.xml' \
        >"$WORK/cut/org.acme.todos/build.properties"
    mvn_in cut cut.log package -pl org.acme.todos ||
        fail "cut build: $(tail -n 20 "$WORK/cut.log")"
    classes=$(unzip -l "$WORK/cut/org.acme.todos/target/"*.jar |
        grep -c -e '\.class$' -e ' plugin.xml$' || true)
    [ "$classes" = 0 ] || fail "cut bin.includes still packaged $classes"
    ok "comma list without backslashes: build passes, 0 classes, no plugin.xml"

    fresh_copy nosingleton
    sed 's/;singleton:=true//' "$ROOT/plugin/org.acme.todos/META-INF/MANIFEST.MF" \
        >"$WORK/nosingleton/org.acme.todos/META-INF/MANIFEST.MF"
    if mvn_in nosingleton nosingleton.log verify; then
        fail "tests passed without singleton:=true"
    fi
    grep -q 'are ignored. The bundle is not marked as singleton' \
        "$WORK/nosingleton/org.acme.todos.tests/target/work/data/.metadata/.log" ||
        fail "registry warning not found"
    ok "no singleton: registry ignores the extensions; $(grep -E \
'^Tests run: [0-9]+, Failures' "$WORK/nosingleton.log" | tail -n 1)"

    mkdir -p "$WORK/inst"
    (cd "$WORK/inst" && "$MVN" -B \
        org.eclipse.tycho:tycho-p2-director-plugin:5.0.4:director \
        -Ddestination="$WORK/inst/eclipse" \
        -Drepositories="https://download.eclipse.org/eclipse/updates/4.41/,file:$repo" \
        -DinstallIUs=org.eclipse.platform.ide,org.acme.todos.feature.feature.group \
        -Dprofile=SDKProfile -Droaming=true) >"$WORK/director.log" 2>&1 ||
        fail "director: $(tail -n 20 "$WORK/director.log")"
    home=$(find "$WORK/inst/eclipse" -name plugins -type d -maxdepth 4 |
        head -n 1)
    home=$(dirname "$home")
    launcher=$(find "$home/plugins" -name 'org.eclipse.equinox.launcher_*.jar' |
        head -n 1)
    (printf 'ss org.acme\n'
        sleep 15
        printf 'close\ny\n') |
        (cd "$home" && "$JAVA" -jar "$launcher" -nosplash -console -noExit \
            -application org.eclipse.equinox.p2.director -listInstalledRoots \
            -data "$WORK/inst-ws") >"$WORK/installed.log" 2>&1 || true
    grep -q '^org.acme.todos.feature.feature.group/' "$WORK/installed.log" ||
        fail "feature not installed: $(tail -n 20 "$WORK/installed.log")"
    state=$(grep -E '[0-9]+[[:space:]]+[A-Z]+[[:space:]]+org.acme.todos_' \
        "$WORK/installed.log" | head -n 1)
    [ -n "$state" ] || fail "bundle state not reported"
    ok "p2 director install: feature root installed; ss: $state"
}

"$MODE"
echo "$PASS checks passed ($MODE)"
