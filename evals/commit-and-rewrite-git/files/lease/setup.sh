#!/bin/sh
# Builds lease/remote.git and lease/mine. A colleague pushed a commit to
# origin/feature after the local amend; mine has fetched it in the background.
set -eu
cd "$(dirname "$0")"
rm -rf remote.git mine theirs
git init -q --bare -b main remote.git
git clone -q remote.git mine 2>/dev/null
cd mine
git config user.name Fixture
git config user.email fixture@example.invalid
echo base >a.txt
git add .
git commit -q -m base
git push -q origin main
git switch -q -c feature
echo v1 >b.txt
git add .
git commit -q -m "add b"
git push -q -u origin feature
cd ..
git clone -q -b feature remote.git theirs 2>/dev/null
cd theirs
git config user.name Colleague
git config user.email colleague@example.invalid
echo theirs >c.txt
git add .
git commit -q -m "colleague work"
git push -q origin feature
cd ../mine
git fetch -q origin
git commit -q --amend -m "add b (amended)"
