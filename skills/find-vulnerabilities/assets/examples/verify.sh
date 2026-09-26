#!/usr/bin/env sh
# Runs every vulnerable/fixed example against local, synthetic targets.
#
#   sh verify.sh local     Python tests, Java XXE,
#                          semgrep taint rule, gitleaks/trufflehog/regex
#                          secret scans, finding checker (default)
#   sh verify.sh network   third-party examples through uv, and dependency
#                          audits (cargo audit, bun audit, pip-audit,
#                          osv-scanner) on manifests generated in a temp dir
#   sh verify.sh all       both
#
# A missing tool prints SKIP; a check that runs and fails exits 1.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../.." && pwd)
MODE=${1:-local}
case "$MODE" in
    local | network | all) ;;
    *)
        echo 'usage: verify.sh [local|network|all]' >&2
        exit 2
        ;;
esac
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM

have() { command -v "$1" >/dev/null 2>&1; }
fail() {
    echo "FAIL $*" >&2
    exit 1
}

python_tests() {
    for test in "$ROOT"/python/test_*.py "$SKILL"/scripts/test_*.py; do
        "$PY" "$test" 2>"$WORK/test.log" || {
            cat "$WORK/test.log" >&2
            fail "$test"
        }
        echo "PASS $(basename "$test") ($(tail -1 "$WORK/test.log"))"
    done
}

java_xxe() {
    if ! have java; then
        echo 'SKIP java: not installed'
        return 0
    fi
    printf 'SYNTHETIC-SECRET\n' >"$WORK/secret.txt"
    java "$ROOT/java/Xxe.java" vulnerable "$WORK/secret.txt" \
        >"$WORK/xxe.log" 2>&1
    grep -q 'parsed text=SYNTHETIC-SECRET' "$WORK/xxe.log" ||
        fail 'default DocumentBuilderFactory did not read the file'
    java "$ROOT/java/Xxe.java" fixed "$WORK/secret.txt" >"$WORK/xxe.log" 2>&1
    grep -q '^rejected: DOCTYPE is disallowed' "$WORK/xxe.log"
    grep -q '^plain text=ok' "$WORK/xxe.log"
    echo "PASS java XXE ($(java -version 2>&1 | head -1))"
}

semgrep_rule() {
    if ! have semgrep; then
        echo 'SKIP semgrep: not installed'
        return 0
    fi
    semgrep scan --metrics=off --disable-version-check --quiet \
        --config "$ROOT/semgrep/sql-taint.yaml" --json \
        "$ROOT/semgrep/handlers.py" >"$WORK/sg.json"
    lines=$("$PY" -c 'import json,sys
print(sorted(r["start"]["line"] for r in json.load(sys.stdin)["results"]))' \
        <"$WORK/sg.json")
    flagged=$(grep -n 'CWE-89: flagged' "$ROOT/semgrep/handlers.py" |
        cut -d: -f1)
    [ "$lines" = "[$flagged]" ] || fail "semgrep flagged $lines"
    echo "PASS semgrep taint rule flags only line $flagged"
}

make_leaky_tree() {
    mkdir -p "$1"
    "$PY" - "$1/settings.py" <<'PY'
import secrets, string, sys
upper = string.ascii_uppercase + "234567"  # base32, like real key IDs
alnum = string.ascii_letters + string.digits
aws = "AK" + "IA" + "".join(secrets.choice(upper) for _ in range(16))
gh = "gh" + "p_" + "".join(secrets.choice(alnum) for _ in range(36))
with open(sys.argv[1], "w") as f:
    f.write(f'AWS_ACCESS_KEY_ID = "{aws}"\nGITHUB_TOKEN = "{gh}"\n')
PY
}

secret_scans() {
    make_leaky_tree "$WORK/leaky"
    status=0
    "$PY" "$SKILL/scripts/scan_secrets.py" "$WORK/leaky" >"$WORK/scan.log" ||
        status=$?
    [ "$status" -eq 1 ] || fail 'regex scanner missed the synthetic keys'
    grep -q 'aws-access-key-id' "$WORK/scan.log"
    grep -q 'github-token' "$WORK/scan.log"
    echo 'PASS scan_secrets.py finds both synthetic keys (redacted)'
    if have gitleaks; then
        status=0
        gitleaks dir --no-banner --redact -f json -r "$WORK/gl.json" \
            "$WORK/leaky" 2>/dev/null || status=$?
        [ "$status" -eq 1 ] || fail "gitleaks exit $status"
        grep -q '"RuleID": "aws-access-token"' "$WORK/gl.json"
        grep -q '"RuleID": "github-pat"' "$WORK/gl.json"
        grep -q '"Secret": "REDACTED"' "$WORK/gl.json"
        echo "PASS gitleaks $(gitleaks version) finds both, redacted"
    else
        echo 'SKIP gitleaks: not installed'
    fi
    if have trufflehog; then
        trufflehog filesystem --no-verification --no-update --json \
            "$WORK/leaky" 2>/dev/null >"$WORK/th.json"
        grep -q '"DetectorName":"Github"' "$WORK/th.json"
        grep -q '"Verified":false' "$WORK/th.json"
        echo 'PASS trufflehog --no-verification reports unverified GitHub key'
    else
        echo 'SKIP trufflehog: not installed'
    fi
}

finding_checker() {
    "$PY" "$SKILL/scripts/check_findings.py" "$ROOT/review.md"
    echo 'PASS review.md findings are complete'
}

third_party() {
    if ! have uv; then
        echo 'SKIP third-party examples: uv not installed'
        return 0
    fi
    for pair in autoescape_jinja2:jinja2 defused_xml:defusedxml \
        argon2_hash:argon2-cffi; do
        script=${pair%%:*}
        package=${pair#*:}
        uv run --quiet --no-project --with "$package" \
            python "$ROOT/thirdparty/$script.py" || fail "$script"
    done
}

dependency_audits() {
    mkdir -p "$WORK/rs" "$WORK/js" "$WORK/py"
    printf '%s\n' 'version = 3' '' '[[package]]' 'name = "demo"' \
        'version = "0.1.0"' 'dependencies = ["smallvec"]' '' \
        '[[package]]' 'name = "smallvec"' 'version = "1.6.0"' \
        'source = "registry+https://github.com/rust-lang/crates.io-index"' \
        >"$WORK/rs/Cargo.lock"
    if have cargo-audit; then
        status=0
        (cd "$WORK/rs" && cargo audit --json >audit.json 2>/dev/null) ||
            status=$?
        [ "$status" -eq 1 ] || fail "cargo audit exit $status"
        grep -o 'RUSTSEC-[0-9]*-[0-9]*' "$WORK/rs/audit.json" | sort -u
        echo 'PASS cargo audit flags smallvec 1.6.0'
    else
        echo 'SKIP cargo audit: not installed'
    fi
    if have bun; then
        printf '%s\n' '{"name":"demo","private":true,' \
            '"dependencies":{"minimist":"1.2.0"}}' >"$WORK/js/package.json"
        (cd "$WORK/js" && BUN_INSTALL_CACHE_DIR="$WORK/bun" \
            bun install --ignore-scripts >/dev/null 2>&1)
        status=0
        (cd "$WORK/js" && bun audit --json >audit.json 2>/dev/null) ||
            status=$?
        [ "$status" -eq 1 ] || fail "bun audit exit $status"
        grep -o 'GHSA-[a-z0-9-]*' "$WORK/js/audit.json" | sort -u
        echo 'PASS bun audit flags minimist 1.2.0'
    else
        echo 'SKIP bun audit: bun not installed'
    fi
    printf 'pyyaml==5.3.1\n' >"$WORK/py/requirements.txt"
    if have pip-audit; then
        audit='pip-audit'
    elif have uvx; then
        audit='uvx --quiet pip-audit'
    else
        audit=''
    fi
    if [ -n "$audit" ]; then
        status=0
        # shellcheck disable=SC2086 # audit is a command plus arguments
        $audit -r "$WORK/py/requirements.txt" --no-deps --disable-pip \
            -f json -o "$WORK/py/audit.json" 2>/dev/null || status=$?
        [ "$status" -eq 1 ] || fail "pip-audit exit $status"
        grep -o 'PYSEC-[0-9]*-[0-9]*' "$WORK/py/audit.json" | sort -u
        echo "PASS pip-audit ($audit) flags pyyaml 5.3.1"
    else
        echo 'SKIP pip-audit: neither pip-audit nor uvx installed'
    fi
    if have osv-scanner; then
        status=0
        osv-scanner scan -L "$WORK/rs/Cargo.lock" || status=$?
        [ "$status" -ne 0 ] || fail 'osv-scanner found nothing'
        echo 'PASS osv-scanner flags the lockfile'
    else
        echo 'SKIP osv-scanner: not installed'
    fi
}

if [ "$MODE" = local ] || [ "$MODE" = all ]; then
    python_tests
    java_xxe
    semgrep_rule
    secret_scans
    finding_checker
fi
if [ "$MODE" = network ] || [ "$MODE" = all ]; then
    third_party
    dependency_audits
fi
echo 'VERIFY PASSED'
