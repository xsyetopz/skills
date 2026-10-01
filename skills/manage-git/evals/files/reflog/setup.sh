#!/bin/sh
# Builds reflog/repo: two commits were made and then removed by reset --hard.
set -eu
cd "$(dirname "$0")"
rm -rf repo
git init -q -b main repo
cd repo
git config user.name Fixture
git config user.email fixture@example.invalid
echo one >ledger.txt
git add .
git commit -q -m "add ledger"
echo two >>ledger.txt
git commit -q -am "add entry two"
echo three >>ledger.txt
git commit -q -am "add entry three"
git reset -q --hard HEAD~2
