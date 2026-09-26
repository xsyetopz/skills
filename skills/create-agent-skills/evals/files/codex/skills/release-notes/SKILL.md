---
name: release-notes
description: >-
  Drafts release notes from merged pull requests and conventional commits
  between two tags, grouped by user impact. Use when preparing a release
  announcement. Not for CHANGELOG.md maintenance.
---

# Release notes

1. Find the previous tag: `git describe --tags --abbrev=0 HEAD^`.
1. List merged pull requests since that tag with
   `git log --merges --first-parent PREV..HEAD --format='%s%n%b'`.
1. Group entries under Highlights, Fixes, and Breaking changes; drop
   internal refactors and CI changes.
1. Write each entry for a user: what changed for them, not how.
