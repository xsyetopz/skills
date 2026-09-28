#!/usr/bin/env sh
# Runs each local Git operation from the skill in disposable repositories
# with isolated configuration, and asserts the resulting HEAD, index,
# worktree, and refs. Never touches the caller's repositories.
set -eu
command -v git >/dev/null 2>&1 || {
    echo 'SKIP: git not found'
    exit 0
}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
trap 'exit 130' INT
trap 'exit 143' TERM
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL="$WORK/gitconfig"
export GIT_AUTHOR_NAME=fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=fixture GIT_COMMITTER_EMAIL=fixture@example.invalid
git config --global init.defaultBranch main
git config --global commit.gpgSign false
git config --global tag.gpgSign false
git config --global advice.detachedHead false
PASSED=0
pass() {
    PASSED=$((PASSED + 1))
    echo "PASS $1"
}
fail() {
    echo "FAIL $1: $2" >&2
    exit 1
}
new_repo() {
    rm -rf "$1"
    git init -q "$1"
    cd "$1"
    printf 'line 1\nline 2\nline 3\nline 4\nline 5\n' >app.txt
    printf 'readme\n' >README.md
    git add -A
    git commit -q -m 'base'
}

# 1. Three states: HEAD, index, worktree are observed separately.
new_repo "$WORK/states"
echo 'staged' >>README.md
git add README.md
echo 'unstaged' >>app.txt
echo 'new' >untracked.txt
[ "$(git diff --cached --name-only)" = README.md ] || fail states cached
[ "$(git diff --name-only)" = app.txt ] || fail states worktree
[ "$(git status --short | tr '\n' ' ')" = 'M  README.md  M app.txt ?? untracked.txt ' ] ||
    fail states "$(git status --short)"
pass 'status/diff/diff --cached separate index, worktree, untracked'

# 2. Partial staging without an interactive prompt: stage one hunk.
new_repo "$WORK/partial"
printf 'line 1 CHANGED\nline 2\nline 3\nline 4\nline 5 CHANGED\n' >app.txt
git diff -U0 app.txt >"$WORK/full.patch"
# Keep the first hunk only (header + first @@ block).
awk '/^@@/{n++} n<2' "$WORK/full.patch" >"$WORK/first.patch"
git apply --cached --unidiff-zero "$WORK/first.patch"
[ "$(git show :app.txt | sed -n 1p)" = 'line 1 CHANGED' ] || fail partial idx1
[ "$(git show :app.txt | sed -n 5p)" = 'line 5' ] || fail partial idx5
[ "$(sed -n 5p app.txt)" = 'line 5 CHANGED' ] || fail partial worktree
pass 'git apply --cached staged one hunk; the other stays unstaged'

# 3. commit --only records the path's worktree content, not staged hunks.
git commit -q --only -m 'only' -- app.txt
[ "$(git show HEAD:app.txt | sed -n 5p)" = 'line 5 CHANGED' ] ||
    fail commit-only 'expected the unstaged hunk to be committed'
pass 'commit --only -- path committed the unstaged hunk as well'

# 4. Snapshot identity: write-tree before commit equals HEAD^{tree} after.
new_repo "$WORK/tree"
echo 'feature' >>app.txt
git add app.txt
expected=$(git write-tree)
git commit -q -m 'feature'
[ "$(git rev-parse 'HEAD^{tree}')" = "$expected" ] || fail tree mismatch
pass 'write-tree before commit equals HEAD^{tree} after'

# 5. A hook that edits the index changes the committed tree.
mkdir -p "$WORK/hooks"
cat >"$WORK/hooks/pre-commit" <<'EOF'
#!/bin/sh
echo 'added by hook' >>README.md
git add README.md
EOF
chmod +x "$WORK/hooks/pre-commit"
echo 'second' >>app.txt
git add app.txt
expected=$(git write-tree)
git -c core.hooksPath="$WORK/hooks" commit -q -m 'with hook'
[ "$(git rev-parse 'HEAD^{tree}')" != "$expected" ] ||
    fail hook-tree 'expected the hook to change the tree'
pass 'pre-commit hook changed the committed tree; write-tree detects it'

# 6. Fixup commit squashed non-interactively with --autosquash.
new_repo "$WORK/fixup"
echo 'feature' >feature.txt
git add feature.txt
git commit -q -m 'feat: add feature'
target=$(git rev-parse HEAD)
echo 'other' >other.txt
git add other.txt
git commit -q -m 'chore: other'
echo 'typo fix' >>feature.txt
git add feature.txt
git commit -q --fixup "$target"
GIT_SEQUENCE_EDITOR=true git rebase -q -i --autosquash HEAD~3
[ "$(git log --format=%s | tr '\n' '|')" = 'chore: other|feat: add feature|base|' ] ||
    fail autosquash "$(git log --oneline)"
[ "$(git show HEAD~1:feature.txt | tail -1)" = 'typo fix' ] ||
    fail autosquash 'fixup content missing'
pass 'commit --fixup + rebase -i --autosquash folded the fix'

# 7. Recovery ref and reflog: a hard reset is undone.
new_repo "$WORK/recover"
echo 'work' >>app.txt
git commit -q -am 'important work'
lost=$(git rev-parse HEAD)
git reset -q --hard HEAD~1
git reflog | grep -q 'important work' || fail reflog 'not in reflog'
git branch rescue 'HEAD@{1}'
[ "$(git rev-parse rescue)" = "$lost" ] || fail reflog 'wrong rescue'
pass 'reflog entry HEAD@{1} restored the commit after reset --hard'

# 8. Stash with untracked files and index restoration.
new_repo "$WORK/stash"
echo 'staged' >>README.md
git add README.md
echo 'unstaged' >>app.txt
echo 'untracked' >notes.txt
git stash push -q -u -m 'before integration'
[ -z "$(git status --porcelain)" ] || fail stash 'tree not clean'
git stash apply -q --index
[ "$(git diff --cached --name-only)" = README.md ] || fail stash index
[ "$(git diff --name-only)" = app.txt ] || fail stash worktree
[ -f notes.txt ] || fail stash untracked
pass 'stash push -u then apply --index restored all three states'

# 9. Merge policies: --ff-only refuses divergence; --no-ff records a merge.
new_repo "$WORK/merge"
git checkout -q -b topic
echo 'topic' >topic.txt
git add topic.txt
git commit -q -m 'topic'
git checkout -q main
echo 'main' >main.txt
git add main.txt
git commit -q -m 'main change'
if git merge -q --ff-only topic 2>/dev/null; then
    fail ff-only 'merged despite divergence'
fi
git merge -q --no-ff -m 'merge topic' topic
[ "$(git rev-list --parents -n1 HEAD | wc -w | tr -d ' ')" -eq 3 ] ||
    fail no-ff 'not a merge commit'
pass 'merge --ff-only refused divergence; --no-ff created a merge'

# 10. Rebase conflict: "ours" is the upstream side during a rebase.
new_repo "$WORK/ours"
git checkout -q -b feature
sed -i.bak 's/line 3/line 3 FEATURE/' app.txt && rm app.txt.bak
git commit -q -am 'feature edit'
git checkout -q main
sed -i.bak 's/line 3/line 3 MAIN/' app.txt && rm app.txt.bak
git commit -q -am 'main edit'
git checkout -q feature
if git rebase -q main >/dev/null 2>&1; then fail rebase 'expected conflict'; fi
[ "$(git diff --name-only --diff-filter=U)" = app.txt ] || fail rebase unmerged
git checkout --ours app.txt
grep -q 'line 3 MAIN' app.txt || fail rebase-ours 'ours was not upstream'
git checkout --theirs app.txt
grep -q 'line 3 FEATURE' app.txt || fail rebase-theirs 'theirs not feature'
git rebase --abort
[ "$(git log -1 --format=%s)" = 'feature edit' ] || fail rebase abort
pass 'during rebase, --ours is upstream (main) and --theirs is the feature'

# 11. Cherry-pick -x records the source commit.
new_repo "$WORK/pick"
git checkout -q -b fix
echo 'fix' >fix.txt
git add fix.txt
git commit -q -m 'fix: bug'
source=$(git rev-parse HEAD)
git checkout -q main
git cherry-pick -x "$source" >/dev/null
git log -1 --format=%B | grep -q "cherry picked from commit $source" ||
    fail cherry-pick 'no -x trailer'
pass 'cherry-pick -x recorded the source commit'

# 12. Revert a merge commit with -m 1.
cd "$WORK/merge"
git revert --no-edit -m 1 HEAD >/dev/null
[ ! -e topic.txt ] || fail revert-merge 'topic change still present'
pass 'revert -m 1 of a merge removed the merged branch changes'

# 13. reset modes and restore: each moves only what it names.
new_repo "$WORK/reset"
echo 'x' >>app.txt
git commit -q -am 'x'
git reset -q --soft HEAD~1
[ "$(git diff --cached --name-only)" = app.txt ] || fail reset-soft index
git reset -q --mixed HEAD
[ -z "$(git diff --cached --name-only)" ] || fail reset-mixed index
[ "$(git diff --name-only)" = app.txt ] || fail reset-mixed worktree
git add app.txt
git restore --staged app.txt
[ "$(git diff --name-only)" = app.txt ] || fail restore-staged worktree
git restore app.txt
[ -z "$(git status --porcelain)" ] || fail restore worktree
pass 'reset --soft/--mixed and restore --staged/restore moved one state each'

# 14. Annotated tag points at the reviewed commit.
git tag -a v1.0.0 -m 'release 1.0.0' HEAD
[ "$(git cat-file -t v1.0.0)" = tag ] || fail tag 'not annotated'
[ "$(git rev-parse 'v1.0.0^{commit}')" = "$(git rev-parse HEAD)" ] ||
    fail tag 'wrong target'
pass 'annotated tag object peels to the reviewed commit'

# 15. force-with-lease refuses when the remote moved.
git init -q --bare "$WORK/remote.git"
new_repo "$WORK/clone-a"
git remote add origin "$WORK/remote.git"
git push -q origin main
git clone -q "$WORK/remote.git" "$WORK/clone-b"
(cd "$WORK/clone-b" && echo b >b.txt && git add b.txt &&
    git commit -q -m 'from b' && git push -q origin main)
cd "$WORK/clone-a"
expected=$(git rev-parse origin/main)
git commit -q --amend -m 'rewritten base'
if git push -q --force-with-lease="refs/heads/main:$expected" origin main \
    2>/dev/null; then
    fail lease 'push overwrote a remote update'
fi
pass 'force-with-lease rejected the push after the remote moved'

# 16. Worktree: separate checkout and index, shared refs.
new_repo "$WORK/wt"
git worktree add -q -b investigate "$WORK/wt-investigate" HEAD
(cd "$WORK/wt-investigate" && echo i >i.txt && git add i.txt &&
    git commit -q -m 'investigation')
[ "$(git log -1 --format=%s investigate)" = investigation ] || fail wt ref
[ -z "$(git status --porcelain)" ] || fail wt 'main checkout changed'
git worktree remove "$WORK/wt-investigate"
pass 'worktree commit visible on its branch; main checkout untouched'

echo "VERIFY PASSED: $PASSED checks"
