#!/usr/bin/env sh
# Verifies the build-and-debug-pcsx2 examples.
#
#   verify.sh            offline (default, about 3 s): script tests, the PNACH
#                        checker on good/bad/warn fixtures, command builder.
#   verify.sh release    opt-in, macOS only: downloads the official PCSX2
#                        v2.8.2 macOS release (24 MB, 110 MB unpacked, runs
#                        under Rosetta on arm64) into a temp directory and
#                        checks -help, unknown options, -batch without a
#                        target, -datapath, portable.txt, -logfile, the
#                        first-run wizard flag, and the no-BIOS exit status.
#                        Needs network. Never touches the normal profile.
#   verify.sh build      opt-in: clones PCSX2 at the pinned commit and runs
#                        the upstream macOS or Linux dependency script,
#                        configure, and build. Cost measured step by step
#                        on one shared 10-core arm64 Mac (machine-specific):
#                        150 MB clone, 170 MB source tarballs, 4.5 GB peak
#                        disk, about 20 min for the dependencies (17 min of
#                        it Qt); ninja then ran 904 of 1006 steps in 65 s
#                        before the Metal shader step failed. On macOS it
#                        needs Xcode, nasm, and the Metal Toolchain; it is
#                        not a supported arm64 build. PCSX2_WORK keeps the tree;
#                        PCSX2_TARGET=unittests builds and runs only the
#                        upstream unit tests (no Metal shaders needed).
# No mode downloads or uses a BIOS, disc image, or other guest content.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SCRIPTS="$ROOT/../../scripts"
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
PCSX2_SHA=2c804670c5f2c99d6a6b842904dd222de89aa493
RELEASE_URL=https://github.com/PCSX2/pcsx2/releases/download/v2.8.2
RELEASE_TAR=pcsx2-v2.8.2-macos-Qt.tar.xz
RELEASE_SHA256=3ed9eb40a33eae67134142c24255a079be444f0616ca29575a04a37981f7d426

fail() { echo "FAIL $*" >&2; exit 1; }

# Some macOS SDK/linker pairs cannot link (ld: tapi error); fall back to the
# first installed SDK that links a trivial program.
pick_sdk() {
    probe=$(mktemp -d "${TMPDIR:-/tmp}/pcsx2-sdk.XXXXXX")
    printf 'int main(void){return 0;}\n' >"$probe/t.c"
    if cc "$probe/t.c" -o "$probe/t" 2>/dev/null; then
        rm -rf "$probe"
        return 0
    fi
    for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX*.*.sdk; do
        if SDKROOT="$sdk" cc "$probe/t.c" -o "$probe/t" 2>/dev/null; then
            export SDKROOT="$sdk"
            echo "NOTE using SDKROOT=$sdk"
            rm -rf "$probe"
            return 0
        fi
    done
    rm -rf "$probe"
    return 1
}

offline() {
    "$PY" "$SCRIPTS/test_check_pnach.py"
    "$PY" "$SCRIPTS/test_build_command.py"
    "$PY" "$SCRIPTS/check_pnach.py" "$ROOT"/pnach/good/*.pnach
    echo 'PASS good PNACH fixture: 0 errors, 0 warnings'
    status=0
    out=$("$PY" "$SCRIPTS/check_pnach.py" "$ROOT"/pnach/bad/*.pnach) ||
        status=$?
    [ "$status" -eq 1 ] || fail "bad fixtures exited $status, expected 1"
    echo "$out" | tail -1 | grep -q '^11 errors' ||
        fail "expected 11 errors: $out"
    echo 'PASS bad PNACH fixtures: 11 loader errors, exit 1'
    "$PY" "$SCRIPTS/check_pnach.py" "$ROOT"/pnach/warn/*.pnach >/dev/null
    echo 'PASS warn PNACH fixtures: warnings only, exit 0'
    "$PY" "$SCRIPTS/build_command.py" --format posix --exe pcsx2-qt \
        --batch --no-gui --data-path /case/data \
        --log-file /case/emulog.txt --elf /case/test.elf
    echo 'PASS command builder prints an argv without launching'
}

run_bounded() { # seconds, command...: kill after the bound (no timeout(1))
    secs=$1
    shift
    perl -e 'alarm(shift); exec(@ARGV) or die "exec: $!"' "$secs" "$@"
}

release() {
    [ "$(uname -s)" = Darwin ] || fail 'release mode needs macOS'
    work=$(mktemp -d "${TMPDIR:-/tmp}/pcsx2-verify.XXXXXX")
    trap 'rm -rf "$work"' 0
    profile="$HOME/Library/Application Support/PCSX2"
    touch "$work/stamp"
    curl -sSfL -o "$work/$RELEASE_TAR" "$RELEASE_URL/$RELEASE_TAR"
    echo "$RELEASE_SHA256  $work/$RELEASE_TAR" | shasum -a 256 -c -
    tar -xf "$work/$RELEASE_TAR" -C "$work"
    app="$work/PCSX2-v2.8.2.app"
    bin="$app/Contents/MacOS/PCSX2"

    status=0
    run_bounded 30 "$bin" -help >"$work/help.txt" 2>&1 || status=$?
    [ "$status" -eq 1 ] || fail "-help exited $status, expected 1"
    grep -q -- '-datapath <path>' "$work/help.txt" || fail 'no -datapath'
    echo 'PASS -help prints the option list and exits 1'

    for args in '-nosuchflag' '-batch'; do
        status=0
        # shellcheck disable=SC2086 # one word per case, split on purpose
        run_bounded 30 "$bin" -datapath "$work" $args >/dev/null 2>&1 ||
            status=$?
        [ "$status" -eq 1 ] || fail "$args exited $status, expected 1"
    done
    echo 'PASS unknown option and target-less -batch exit 1'

    status=0
    run_bounded 60 "$bin" -datapath "$work/missing" -logfile \
        "$work/missing.log" -testconfig >/dev/null 2>&1 || status=$?
    [ "$status" -eq 1 ] || fail "missing datapath exited $status"
    [ ! -e "$work/missing" ] || fail 'missing datapath was created'
    echo 'PASS -datapath to a missing directory exits 1 and creates nothing'

    mkdir "$work/data"
    run_bounded 60 "$bin" -datapath "$work/data" -logfile "$work/tc.log" \
        -testconfig >/dev/null 2>&1
    ini="$work/data/PCSX2/inis/PCSX2.ini"
    [ -f "$ini" ] || fail "no $ini"
    grep -q 'DataRoot Directory: .*/data/PCSX2$' "$work/tc.log" ||
        fail 'DataRoot line missing from -logfile output'
    echo 'PASS -testconfig writes DATAPATH/PCSX2/inis/PCSX2.ini; log at -logfile'

    mkdir "$work/portable"
    cp -R "$app" "$work/portable/"
    printf 'userdata\n' >"$work/portable/portable.txt"
    run_bounded 60 "$work/portable/PCSX2-v2.8.2.app/Contents/MacOS/PCSX2" \
        -testconfig >/dev/null 2>&1
    [ -f "$work/portable/userdata/inis/PCSX2.ini" ] ||
        fail 'portable.txt did not redirect data'
    echo 'PASS portable.txt beside the .app puts data in its named subdir'

    grep -q '^SetupWizardIncomplete = true' "$ini" ||
        fail 'fresh profile should mark the wizard incomplete'
    sed 's/^SetupWizardIncomplete = true/SetupWizardIncomplete = false/' \
        "$ini" >"$ini.new" && mv "$ini.new" "$ini"
    printf 'not an elf' >"$work/dummy.elf"
    status=0
    run_bounded 60 "$bin" -datapath "$work/data" -logfile "$work/boot.log" \
        -batch -nogui -elf "$work/dummy.elf" >/dev/null 2>&1 || status=$?
    [ "$status" -eq 0 ] || fail "no-BIOS batch run exited $status"
    grep -q 'requires a PlayStation 2 BIOS' "$work/boot.log" ||
        fail 'expected the BIOS startup error in the log'
    grep -q 'Savestate version: 0x9a590000' "$work/boot.log" ||
        fail 'expected the save-state version line'
    echo 'PASS no-BIOS batch boot exits 0; only the log shows the failure'

    if [ -d "$profile" ] &&
        [ -n "$(find "$profile" -newer "$work/stamp" | head -1)" ]; then
        fail "normal profile changed: $profile"
    fi
    echo 'PASS normal profile untouched'
}

build() {
    work=${PCSX2_WORK:-$(mktemp -d "${TMPDIR:-/tmp}/pcsx2-build.XXXXXX")}
    echo "NOTE build tree: $work (cost: see header of this script)"
    if [ ! -d "$work/pcsx2/.git" ]; then
        git init -q "$work/pcsx2"
        git -C "$work/pcsx2" remote add origin \
            https://github.com/PCSX2/pcsx2.git
    fi
    git -C "$work/pcsx2" fetch -q --depth 1 origin "$PCSX2_SHA"
    git -C "$work/pcsx2" checkout -q FETCH_HEAD
    src="$work/pcsx2"
    case "$(uname -s)" in
    Darwin)
        pick_sdk || fail 'no macOS SDK can link a C program'
        command -v nasm >/dev/null || echo 'WARN nasm missing: FFmpeg fails'
        xcrun metal -v >/dev/null 2>&1 ||
            echo 'WARN Metal Toolchain missing: shader step fails'
        (cd "$work" && "$src/.github/workflows/scripts/macos/build-dependencies.sh" \
            "$work/deps")
        cmake -S "$src" -B "$work/build" -G Ninja \
            -DCMAKE_PREFIX_PATH="$work/deps" -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_OSX_ARCHITECTURES=x86_64 -DUSE_LINKED_FFMPEG=ON
        ;;
    Linux)
        (cd "$work" && "$src/.github/workflows/scripts/linux/build-dependencies-qt.sh" \
            "$work/deps")
        cmake -S "$src" -B "$work/build" -G Ninja \
            -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
            -DCMAKE_EXE_LINKER_FLAGS_INIT=-fuse-ld=lld \
            -DCMAKE_MODULE_LINKER_FLAGS_INIT=-fuse-ld=lld \
            -DCMAKE_SHARED_LINKER_FLAGS_INIT=-fuse-ld=lld \
            -DCMAKE_PREFIX_PATH="$work/deps" -DCMAKE_BUILD_TYPE=Release
        ;;
    *) fail 'build mode supports macOS and Linux' ;;
    esac
    cmake --build "$work/build" --target "${PCSX2_TARGET:-all}"
    echo "PASS built at $work/build"
}

case "${1:-offline}" in
offline) offline ;;
release) offline && release ;;
build) build ;;
*) fail "usage: $0 [offline|release|build]" ;;
esac
echo 'VERIFY PASSED'
