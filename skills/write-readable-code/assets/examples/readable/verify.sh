#!/usr/bin/env sh
# Verifies the write-readable-code examples and layout templates in a
# disposable copy.
#
#   sh verify.sh examples   behavior tests + metric deltas for the refactors
#   sh verify.sh types      typed identifiers reject swapped arguments
#   sh verify.sh layout     every layout template compiles/parses (and runs
#                           where the language allows)
#   sh verify.sh all        all of the above (default)
#
# A missing toolchain prints SKIP and does not fail; a check that runs and
# fails exits 1.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SKILL=$(CDPATH='' cd -- "$ROOT/../../.." && pwd)
MODE=${1:-all}
case "$MODE" in
    all | examples | types | layout) ;;
    *)
        echo 'usage: verify.sh [all|examples|types|layout]' >&2
        exit 2
        ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
PY=${PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1

have() { command -v "$1" >/dev/null 2>&1; }
skip() { echo "SKIP $1: $2 not found"; }
pass() { echo "PASS $1"; }

metric() {
    # metric FILE FUNCTION FIELD -> prints one metric value
    "$PY" "$SKILL/scripts/python_function_metrics.py" --json "$1" |
        "$PY" -c 'import json,sys; rows=json.load(sys.stdin); '\
'print(next(r[sys.argv[2]] for r in rows if r["name"]==sys.argv[1]))' \
            "$2" "$3"
}

expect_lower() {
    # expect_lower LABEL FILE BASELINE CANDIDATE FIELD
    before=$(metric "$2" "$3" "$5")
    after=$(metric "$2" "$4" "$5")
    if [ "$after" -ge "$before" ]; then
        echo "FAIL $1: $5 $before -> $after (expected lower)" >&2
        exit 1
    fi
    echo "PASS $1: $5 $before -> $after"
}

examples() {
    cp -R "$ROOT/python" "$WORK/python"
    "$PY" "$WORK/python/test_examples.py"
    shape="$WORK/python/shape.py"
    expect_lower guard-clauses "$shape" baseline_ship_order \
        candidate_ship_order nesting
    expect_lower phases "$shape" baseline_invoice_total \
        candidate_invoice_total nesting
    expect_lower parameter-object "$shape" baseline_connect_url \
        candidate_connect_url params
    expect_lower dispatch-table "$shape" baseline_apply candidate_apply ccn
    expect_lower flag-argument "$shape" baseline_format_amount \
        format_amount ccn
    "$PY" "$SKILL/scripts/test_python_function_metrics.py"
    "$PY" "$SKILL/scripts/test_term_report.py"
}

types() {
    mkdir -p "$WORK/types"
    cp "$ROOT/types/"* "$ROOT/python/names_types.py" "$WORK/types/"
    cd "$WORK/types"
    if have rustc; then
        rustc --edition 2024 --crate-type lib --emit=metadata \
            -o ids.rmeta ids.rs
        if rustc --edition 2024 --crate-type lib --emit=metadata \
            -o bad.rmeta ids_misuse.rs 2>rust.log; then
            echo 'FAIL rust: swapped ids compiled' >&2
            exit 1
        fi
        grep -q 'E0308' rust.log
        pass 'rust newtype rejects swapped ids (E0308)'
    else
        skip rust rustc
    fi
    TSC=$(command -v tsc || true)
    if [ -z "$TSC" ] && [ -x "$SKILL/../../node_modules/.bin/tsc" ]; then
        TSC="$SKILL/../../node_modules/.bin/tsc"
    fi
    if [ -n "$TSC" ]; then
        "$TSC" --noEmit --strict ids.ts
        if "$TSC" --noEmit --strict ids_misuse.ts >ts.log 2>&1; then
            echo 'FAIL ts: swapped ids type-checked' >&2
            exit 1
        fi
        grep -q 'TS2345' ts.log
        pass 'typescript brands reject swapped ids (TS2345)'
    else
        skip typescript tsc
    fi
    PYRIGHT=$(command -v pyright || true)
    if [ -z "$PYRIGHT" ] && [ -x "$SKILL/../../node_modules/.bin/pyright" ]; then
        PYRIGHT="$SKILL/../../node_modules/.bin/pyright"
    fi
    if [ -n "$PYRIGHT" ]; then
        cat >misuse.py <<'EOF'
from names_types import TenantId, UserId, candidate_membership_key

candidate_membership_key(TenantId(3), UserId(7))
EOF
        if "$PYRIGHT" misuse.py >py.log 2>&1; then
            echo 'FAIL python: swapped NewType ids type-checked' >&2
            exit 1
        fi
        grep -q 'reportArgumentType' py.log
        pass 'pyright NewType rejects swapped ids (reportArgumentType)'
    else
        skip python-types pyright
    fi
    cd "$WORK"
}

layout() {
    L="$SKILL/assets/layout"
    mkdir -p "$WORK/layout"
    cd "$WORK/layout"

    "$PY" -c 'import runpy,sys; m=runpy.run_path(sys.argv[1]); '\
'assert m["public_function"]().public_method()=="{\"state\": 1}"' \
        "$L/python/template.py"
    pass python

    if have rustc; then
        rustc --edition 2024 -D warnings --test -o rs_tests \
            "$L/rust/template.rs"
        ./rs_tests --quiet >/dev/null
        pass rust
    else skip rust rustc; fi

    if have go; then
        mkdir -p go && cp "$L/go/template.go" go/component.go
        printf 'module example.com/component\n\ngo 1.22\n' >go/go.mod
        (cd go && go vet ./...)
        pass go
    else skip go go; fi

    if have cc; then
        cp "$L/c/template.h" component.h
        cc -std=c17 -Wall -Wextra -Werror -I. -c "$L/c/template.c" -o c.o
        pass c
    else skip c cc; fi

    if have c++; then
        cp "$L/cpp/template.hpp" component.hpp
        c++ -std=c++20 -Wall -Wextra -Werror -I. -c "$L/cpp/template.cpp" \
            -o cpp.o
        pass cpp
    else skip cpp c++; fi

    if have dotnet; then
        mkdir -p cs fs
        cp "$L/dotnet/template.cs" cs/Template.cs
        cat >cs/cs.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
EOF
        dotnet build cs/cs.csproj -v q --nologo >/dev/null
        pass csharp
        cp "$L/dotnet/template.fs" fs/Template.fs
        cat >fs/fs.fsproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="Template.fs" />
  </ItemGroup>
</Project>
EOF
        dotnet build fs/fs.fsproj -v q --nologo >/dev/null
        pass fsharp
    else skip dotnet dotnet; fi

    if have javac; then
        mkdir -p java && cp "$L/jvm/template.java" java/PublicType.java
        javac -Xlint:all -Werror -d java/out java/PublicType.java
        pass java
    else skip java javac; fi

    if have kotlinc; then
        kotlinc -Werror "$L/jvm/template.kt" -d kt.jar 2>kt.log ||
            { cat kt.log >&2; exit 1; }
        pass kotlin
    else skip kotlin kotlinc; fi

    if have scala-cli; then
        mkdir -p scala && cp "$L/jvm/template.scala" scala/Template.scala
        scala-cli compile --server=false scala/Template.scala \
            >scala.log 2>&1 || { cat scala.log >&2; exit 1; }
        pass scala
    else skip scala scala-cli; fi

    if have node; then
        node --check "$L/js-ts/template.js"
        pass javascript
    else skip javascript node; fi
    TSC=$(command -v tsc || true)
    if [ -z "$TSC" ] && [ -x "$SKILL/../../node_modules/.bin/tsc" ]; then
        TSC="$SKILL/../../node_modules/.bin/tsc"
    fi
    if [ -n "$TSC" ]; then
        mkdir -p ts && cp "$L/js-ts/template.ts" ts/template.ts
        echo 'export const dependency = 1;' >ts/dependency.ts
        "$TSC" --noEmit --strict --module nodenext \
            --moduleResolution nodenext ts/template.ts
        pass typescript
    else skip typescript tsc; fi

    if have lua; then
        LUA_TEMPLATE="$L/lua/template.lua" lua -e '
            local m = dofile(os.getenv("LUA_TEMPLATE"))
            assert(m.public_function(3):describe() == "PublicType(6)")'
        pass lua
    else skip lua lua; fi

    if have ruby; then
        ruby -w -e 'require ARGV[0]
            raise "bad" unless Component::PublicType.new.public_method ==
                "{\"state\":2}"' "$L/ruby/template.rb"
        pass ruby
    else skip ruby ruby; fi

    # On macOS prefer Xcode's driver: a swiftly toolchain can reject the
    # installed SDK's arguments ("unknown argument: -target-arch-variant").
    if have xcrun; then
        xcrun swiftc -parse-as-library -typecheck "$L/swift/template.swift"
        pass swift
    elif have swiftc; then
        swiftc -parse-as-library -typecheck "$L/swift/template.swift"
        pass swift
    else skip swift swiftc; fi
    cd "$WORK"
}

case "$MODE" in
    examples) examples ;;
    types) types ;;
    layout) layout ;;
    all)
        examples
        types
        layout
        ;;
esac
echo "VERIFY PASSED: $MODE"
