#!/usr/bin/env sh
# Drafts entries from a Conventional Commits history, audits a valid and a
# broken changelog, and checks SemVer strings. Uses a throwaway repository.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SCRIPTS=$(CDPATH='' cd -- "$ROOT/../../scripts" && pwd)
PY=${PYTHON:-python3}
command -v git >/dev/null 2>&1 || {
    echo 'SKIP: git not found'
    exit 0
}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/gitconfig"
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
export PYTHONDONTWRITEBYTECODE=1

git init -q "$WORK/repo"
cd "$WORK/repo"
c() { git commit -q --allow-empty -m "$1" ${2:+-m "$2"}; }
c 'chore: initial'
git tag v1.0.0
c 'feat(export): add cancel endpoint'
c 'fix: remove temp file when validation fails'
c 'docs: describe cancellation'
c 'refactor: extract publisher'
c 'Update dependencies'
draft=$("$PY" "$SCRIPTS/draft_entries.py" v1.0.0..HEAD --version 1.1.0 \
    --date 2026-09-20)
echo "$draft"
echo "$draft" | grep -q '^### Added$'
echo "$draft" | grep -q 'export: add cancel endpoint'
echo "$draft" | grep -q '^### Fixed$'
echo "$draft" | grep -q 'Update dependencies'   # unclassified, not dropped
if echo "$draft" | grep -q 'describe cancellation'; then
    echo 'FAIL docs commit should be omitted' >&2
    exit 1
fi
echo "$draft" | grep -q 'suggested SemVer increment: minor'
echo 'PASS draft groups commits and suggests minor'

c 'feat!: remove v1 export endpoint'
"$PY" "$SCRIPTS/draft_entries.py" v1.0.0..HEAD |
    grep -q 'suggested SemVer increment: major'
echo 'PASS breaking change suggests major'

"$PY" -I "$SCRIPTS/audit_changelog.py" "$ROOT/CHANGELOG.example.md"
echo 'PASS example changelog audits clean'

status=0
"$PY" -I "$SCRIPTS/audit_changelog.py" "$ROOT/CHANGELOG.broken.txt" \
    >"$WORK/broken.log" 2>&1 || status=$?
cat "$WORK/broken.log"
[ "$status" -eq 1 ] || { echo 'FAIL broken changelog passed' >&2; exit 1; }
echo 'PASS broken changelog rejected'

"$PY" -I "$SCRIPTS/audit_semver.py" 1.2.3 2.0.0-rc.1 1.0.0+build.5 >/dev/null
if "$PY" -I "$SCRIPTS/audit_semver.py" v1.2.3 01.2.3 >/dev/null 2>&1; then
    echo 'FAIL invalid SemVer accepted' >&2
    exit 1
fi
echo 'PASS SemVer syntax checks'
"$PY" -I "$SCRIPTS/audit_semver.py" --from-tags >/dev/null
echo 'PASS tags are SemVer'
echo 'VERIFY PASSED'
