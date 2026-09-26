#!/usr/bin/env sh
# Verifies the IntelliJ Platform example plugin in a disposable copy so the
# skill directory never receives build/, .gradle/, or .intellijPlatform/.
#
#   sh verify.sh offline   (default) plugin.xml checker + its tests, pure
#                          logic executed, plugin sources compiled against
#                          an installed IDE's jars (SKIP when none is found)
#   sh verify.sh network   Gradle: test, buildPlugin, ZIP listing, patched
#                          descriptor check, verifyPluginProjectConfiguration,
#                          verifyPluginStructure, verifyPlugin, signPlugin with
#                          a throwaway key, verifyPluginSignature
#   sh verify.sh runide    one bounded runIde attempt (GUI; RUNIDE_SECONDS,
#                          default 240), then the sandbox IDE is stopped
#
# IDE: an installed IntelliJ IDEA 2026.2 (IDE=/path/to/IDE.app, default
# /Applications/IntelliJ IDEA OSS.app). network and runide need gradle 9+
# on PATH and network access for Gradle plugins and the test framework;
# without an IDE, network downloads intellijIdea(platformVersion).
# Never runs publishPlugin.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../.." && pwd)
MODE=${1:-offline}
case "$MODE" in
    offline | network | runide) ;;
    *)
        echo 'usage: verify.sh [offline|network|runide]' >&2
        exit 2
        ;;
esac
IDE=${IDE:-/Applications/IntelliJ IDEA OSS.app}
PY=${PYTHON:-python3}
PYTHONDONTWRITEBYTECODE=1
export PYTHONDONTWRITEBYTECODE
WORK=$(mktemp -d "${TMPDIR:-/tmp}/verify.XXXXXX")
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$ROOT/plugin" "$WORK/plugin"
rm -rf "$WORK/plugin/build" "$WORK/plugin/.gradle" \
    "$WORK/plugin/.intellijPlatform"
SRC="$WORK/plugin/src/main"

have_ide() { [ -d "$IDE/Contents/lib" ]; }

# gradle_run TASK... : Gradle against the local IDE (and its JBR 25) when
# present, otherwise against the downloaded platformVersion.
gradle_run() {
    if have_ide; then
        gradle --console=plain -p "$WORK/plugin" \
            -PplatformLocalPath="$IDE" \
            -Porg.gradle.java.installations.paths="$IDE/Contents/jbr/Contents/Home" \
            "$@"
    else
        gradle --console=plain -p "$WORK/plugin" "$@"
    fi
}

offline() {
    "$PY" "$SKILL/scripts/test_check_plugin_xml.py"
    "$PY" "$SKILL/scripts/check_plugin_xml.py" \
        --src-root "$SRC/kotlin" --src-root "$SRC/java" \
        "$SRC/resources/META-INF/plugin.xml"
    echo 'PASS plugin.xml checker (source descriptor)'

    kotlinc -include-runtime -d "$WORK/logic.jar" \
        "$ROOT/logic/WordTextCheck.kt" \
        "$SRC/kotlin/org/acme/wordstats/WordText.kt" 2>"$WORK/logic.log" ||
        { cat "$WORK/logic.log" >&2; exit 1; }
    java -jar "$WORK/logic.jar"
    echo 'EXECUTED pure logic (WordText.kt)'

    if ! have_ide; then
        echo "SKIP compile against IDE jars: no IDE at $IDE"
        return
    fi
    cp_file="$WORK/classpath.txt"
    find "$IDE/Contents/lib" "$IDE/Contents/plugins/json/lib" \
        -maxdepth 1 -name '*.jar' | tr '\n' ':' >"$cp_file"
    classpath=$(cat "$cp_file")
    mkdir -p "$WORK/classes"
    kotlinc -jvm-target 21 -no-stdlib -no-reflect -Werror \
        -cp "$classpath" -d "$WORK/classes" "$SRC/kotlin" "$SRC/java" \
        2>"$WORK/kotlinc.log" || { cat "$WORK/kotlinc.log" >&2; exit 1; }
    javac -Xlint:all -Werror -d "$WORK/classes" \
        -cp "$classpath:$WORK/classes" \
        "$SRC"/java/org/acme/wordstats/*.java
    echo "COMPILED plugin sources against $IDE (not executed)"
}

network() {
    command -v gradle >/dev/null || { echo 'gradle not on PATH' >&2; exit 1; }
    gradle_run test buildPlugin verifyPluginProjectConfiguration \
        verifyPluginStructure verifyPlugin
    for report in "$WORK"/plugin/build/test-results/test/*.xml; do
        sed -n 's/.*<testsuite name="\([^"]*\)" tests="\([0-9]*\)" skipped="\([0-9]*\)" failures="\([0-9]*\)" errors="\([0-9]*\)".*/TESTS \1: \2 run, \3 skipped, \4 failed, \5 errors/p' \
            "$report"
    done
    unzip -l "$WORK"/plugin/build/distributions/*.zip
    "$PY" "$SKILL/scripts/check_plugin_xml.py" --patched \
        --config-dir "$SRC/resources/META-INF" \
        "$WORK/plugin/build/tmp/patchPluginXml/plugin.xml"
    echo 'PASS plugin.xml checker (patched descriptor)'

    # Throwaway signing material, created and deleted with the temp dir.
    keys="$WORK/keys"
    mkdir -p "$keys"
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 \
        -out "$keys/private.pem" 2>/dev/null
    openssl req -key "$keys/private.pem" -new -x509 -days 1 \
        -subj '/CN=verify-sh-throwaway' -out "$keys/chain.crt"
    PRIVATE_KEY=$(cat "$keys/private.pem")
    CERTIFICATE_CHAIN=$(cat "$keys/chain.crt")
    PRIVATE_KEY_PASSWORD=
    export PRIVATE_KEY CERTIFICATE_CHAIN PRIVATE_KEY_PASSWORD
    # Separate invocations: in 2.19.0 one invocation with both tasks fails
    # Gradle's implicit-dependency validation.
    gradle_run signPlugin
    gradle_run verifyPluginSignature
    ls -l "$WORK"/plugin/build/distributions/
    echo 'NETWORK PASSED'
}

runide() {
    command -v gradle >/dev/null || { echo 'gradle not on PATH' >&2; exit 1; }
    log="$WORK/runide.log"
    gradle_run runIde >"$log" 2>&1 &
    pid=$!
    limit=${RUNIDE_SECONDS:-240}
    waited=0
    loaded=
    while [ "$waited" -lt "$limit" ] && kill -0 "$pid" 2>/dev/null; do
        idea_log=$(sed -n 's/.*IDE logs: \(.*idea\.log\).*/\1/p' "$log" |
            head -n 1)
        if [ -n "$idea_log" ] && [ -f "$idea_log" ]; then
            loaded=$(grep -m 1 'Loaded custom plugins:.*Word Stats Example' \
                "$idea_log" || true)
            [ -n "$loaded" ] && break
        fi
        sleep 5
        waited=$((waited + 5))
    done
    # Stop only this copy's sandbox IDE and Gradle client; never
    # `gradle --stop`, which would kill other builds' daemons.
    pkill -f "$WORK/plugin" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    left=30
    while pgrep -f "$WORK/plugin" >/dev/null 2>&1 && [ "$left" -gt 0 ]; do
        sleep 1
        left=$((left - 1))
    done
    grep -m 1 'IDE logs:' "$log" || tail -n 20 "$log"
    echo "RUNIDE stopped after ${waited}s (limit ${limit}s)"
    if [ -z "$loaded" ]; then
        echo 'RUNIDE FAILED: plugin load line not seen in idea.log' >&2
        exit 1
    fi
    echo "RUNIDE PASSED: $loaded"
}

"$MODE"
