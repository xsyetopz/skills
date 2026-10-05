#!/bin/sh
# Builds partial/repo: parser.py has a real fix and a DEBUG print, README.md is
# staged, notes.txt is untracked.
set -eu
cd "$(dirname "$0")"
rm -rf repo
git init -q -b main repo
cd repo
git config user.name Fixture
git config user.email fixture@example.invalid
cat >parser.py <<'EOF'
def parse(line):
    fields = line.split(",")
    return fields


def total(rows):
    return sum(len(r) for r in rows)
EOF
echo "# csvtool" >README.md
git add .
git commit -q -m "init"
git rev-parse HEAD >../base.txt
cat >parser.py <<'EOF'
def parse(line):
    print("DEBUG parse line:", line)
    fields = line.split(",")
    return fields


def total(rows):
    return sum(len(r) for r in rows if r)
EOF
echo "Handles empty rows." >>README.md
git add README.md
echo "todo" >notes.txt
