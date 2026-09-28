#!/usr/bin/env sh
# Checks every handler, configuration, and tool in a disposable copy.
#
#   sh verify.sh           offline: handler tests on host fixtures, Codex
#                          schema validation, config checks, merge round
#                          trip, OpenCode plugin under bun test
#   sh verify.sh network   also type-checks the OpenCode plugin against
#                          @opencode-ai/plugin@1.18.32 (downloads it)
#
# No agent host is started: a real session would call a model with the
# user's account. Host runs are listed per card as "Not run".
set -eu
SKILL=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
MODE=${1:-verify}
case "$MODE" in
    verify | network) ;;
    *)
        echo 'usage: verify.sh [verify|network]' >&2
        exit 2
        ;;
esac
PYTHON=${PYTHON:-python3}
BUN=${BUN:-bun}
export PYTHONDONTWRITEBYTECODE=1
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
cp -R "$SKILL/." "$WORK/skill"
S="$WORK/skill"
PASS=0

ok() {
    PASS=$((PASS + 1))
    echo "ok   $1"
}

fail() {
    echo "FAIL $1" >&2
    exit 1
}

for test in test_handlers test_merge_and_check test_validate_schema; do
    "$PYTHON" "$S/scripts/$test.py" >"$WORK/$test.log" 2>&1 ||
        fail "$test: $(tail -n 20 "$WORK/$test.log")"
    ok "$test: $(grep -E '^Ran ' "$WORK/$test.log")"
done

# Each host's guard answer on its own fixture.
for pair in claude:claude-pretooluse codex:codex-pretooluse \
    gemini:gemini-beforetool cursor:cursor-pretooluse \
    copilot:copilot-pretooluse copilot-pascal:copilot-pascal-pretooluse \
    vscode:vscode-pretooluse; do
    host=${pair%%:*}
    out=$("$PYTHON" "$S/assets/handlers/guard_shell.py" --host "$host" \
        <"$S/assets/fixtures/${pair#*:}.json") || fail "guard $host"
    case "$out" in
        *'"deny"'*) ok "guard $host: $(printf '%s' "$out" | cut -c1-70)..." ;;
        *) fail "guard $host did not deny: $out" ;;
    esac
done

# Codex fixtures and outputs against the vendored 0.157.0 schemas.
schemas="$S/assets/schemas/codex-0.157.0"
for pair in pre-tool-use:codex-pretooluse stop:codex-stop \
    session-start:codex-sessionstart; do
    "$PYTHON" "$S/scripts/validate_schema.py" \
        "$schemas/${pair%%:*}.command.input.schema.json" \
        "$S/assets/fixtures/${pair#*:}.json" >/dev/null ||
        fail "fixture ${pair#*:} does not match the Codex schema"
done
"$PYTHON" "$S/assets/handlers/guard_shell.py" --host codex \
    <"$S/assets/fixtures/codex-pretooluse.json" >"$WORK/codex-out.json"
"$PYTHON" "$S/scripts/validate_schema.py" \
    "$schemas/pre-tool-use.command.output.schema.json" "$WORK/codex-out.json" \
    >/dev/null || fail "codex guard output does not match the schema"
ok "codex: 3 fixtures and the guard output match the 0.157.0 schemas"

# Each configuration asset, installed into a scratch project.
for host in claude codex gemini cursor copilot vscode; do
    project="$WORK/project-$host"
    cp -R "$S/assets/config/$host/." "$project/"
    mkdir -p "$project/.agent-hooks" "$project/.cursor/hooks"
    cp "$S"/assets/handlers/*.py "$project/.agent-hooks/"
    cp "$S/assets/handlers/guard_shell.py" "$project/.cursor/hooks/"
    file=$(find "$project" -name '*.json' -path '*/.*' | head -n 1)
    "$PYTHON" "$S/scripts/check_hook_config.py" "$file" --host "$host" \
        --project "$project" >"$WORK/check.log" ||
        fail "config $host: $(cat "$WORK/check.log")"
    ok "config $host: $(tail -n 1 "$WORK/check.log")"
done

# Install and roll back one handler without touching other settings.
target="$WORK/merge/.claude/settings.json"
mkdir -p "$(dirname "$target")"
printf '{\n  "permissions": {\n    "deny": ["Read(./.env)"]\n  }\n}\n' >"$target"
cp "$target" "$WORK/merge/original.json"
handler='{"type":"command","command":"python3","args":["guard.py"]}'
"$PYTHON" "$S/scripts/merge_hooks.py" "$target" --host claude \
    --event PreToolUse --matcher Bash --handler "$handler" >/dev/null
"$PYTHON" "$S/scripts/merge_hooks.py" "$target" --host claude \
    --event PreToolUse --matcher Bash --handler "$handler" >/dev/null
count=$(grep -c '"guard.py"' "$target")
[ "$count" -eq 1 ] || fail "second add duplicated the handler ($count)"
"$PYTHON" "$S/scripts/merge_hooks.py" "$target" --host claude \
    --event PreToolUse --matcher Bash --handler "$handler" --remove >/dev/null
"$PYTHON" -c 'import json,sys; a,b=(json.load(open(p)) for p in sys.argv[1:]); sys.exit(a!=b)' \
    "$target" "$WORK/merge/original.json" || fail "remove did not restore"
ok "merge_hooks: add is idempotent; remove restores the original settings"

# OpenCode plugin: run the hook function directly.
if command -v "$BUN" >/dev/null 2>&1; then
    (cd "$S/assets/opencode" && "$BUN" test >"$WORK/bun.log" 2>&1) ||
        fail "opencode: $(cat "$WORK/bun.log")"
    ok "opencode guard: $(grep -E '^ *[0-9]+ pass' "$WORK/bun.log" | tr -d ' ')"
else
    echo "SKIP opencode guard: '$BUN' not found"
fi

if [ "$MODE" = network ]; then
    types="$WORK/opencode-types"
    mkdir -p "$types"
    cp "$S/assets/opencode/guard.ts" "$types/"
    printf '{"private":true,"type":"module"}\n' >"$types/package.json"
    cat >"$types/tsconfig.json" <<'EOF'
{"compilerOptions": {"target": "ES2022", "module": "ESNext",
 "moduleResolution": "bundler", "strict": true, "noEmit": true,
 "allowImportingTsExtensions": true, "skipLibCheck": true},
 "files": ["guard.ts"]}
EOF
    (cd "$types" && "$BUN" add -d @opencode-ai/plugin@1.18.32 \
        typescript@5.9.3 >/dev/null 2>&1 && ./node_modules/.bin/tsc -p .) ||
        fail "opencode guard does not type-check"
    ok "opencode guard type-checks against @opencode-ai/plugin@1.18.32"
fi

for cli in claude codex gemini opencode; do
    if command -v "$cli" >/dev/null 2>&1; then
        echo "info $cli installed: $("$cli" --version 2>/dev/null | head -n 1)" \
            "(not started: a session calls a model)"
    fi
done
echo "$PASS checks passed"
