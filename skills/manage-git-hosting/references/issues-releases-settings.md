# Issues, labels, releases, settings, and CI evidence

The other hosted resources. Sources:

- GitHub: [issues][issues], [releases][releases], [branch protection][bp],
  and [rulesets][rulesets];
- GitLab: [releases][gl-rel] and [protected branches][gl-pb];
- the `gh` help text.

The read commands ran against `cli/cli`. The write commands were not
run; the label sync ran as a dry run.

## Contents

- Create an issue without duplicates
- Label sync
- Release: draft, verify, publish
- Deleting a release versus deleting its tag
- Branch protection and rulesets
- Repository settings
- CI evidence for the reviewed commit

## Create an issue without duplicates

**Definition.** Search for an open issue with the same key, and create
one only if none exists. GitHub closes with `state: closed`; GitLab
closes with `state_event: close`, and its text field is `description`,
not `body`.

**Use when.** Automation or agents file issues, such as flaky-test
reports.

**Do not use when.** The user asked for a new issue even though a similar
one exists. Create it and link the existing one instead of skipping.

**Example.**

```sh
gh issue list -R owner/repo --state open --search 'in:title "flaky: test_x"' \
  --json number --jq '.[0].number'
gh issue create -R owner/repo --title 'flaky: test_x' --label flaky \
  --body-file /tmp/issue.md
```

**Cost removed.** Duplicate issues after retries.

**Verify.**

1. The search ran before the create, and the report shows its result.

## Label sync

**Definition.** Make the repository's labels match a desired list. The
plan is a set of creates, edits, and deletes; name comparison ignores
case; and nothing is deleted without `--prune`.

**Use when.** Standardizing labels across repositories.

**Do not use when.** Other teams own the extra labels; leave `--prune`
off.

**Example.** A dry run against `cli/cli`; nothing was written, and the
account has only `READ`:

```text
$ python3 scripts/sync_labels.py cli/cli labels.json
plan gh label edit bug --color 000000 --description x
```

**Cost removed.** Label drift from hand edits, and accidental deletions.

**Verify.**

1. Show the dry run to the user, then run with `--apply`.
1. A second `--apply` prints "labels already match".

## Release: draft, verify, publish

**Definition.** Create the release as a draft on an existing tag, upload
its assets, check them, and only then publish. With `gh release create`:

- `--verify-tag` aborts if the tag does not exist;
- `--target` sets the commit for a new tag;
- `--latest=false` avoids marking a backport as "Latest".

**Use when.** Any release with assets.

**Do not use when.** The user asked only to prepare notes; a draft is
still a hosted write.

**Example.**

```sh
gh release create v1.4.0 -R owner/repo --draft --verify-tag \
  --title v1.4.0 --notes-file CHANGES.md dist/*.tar.gz
gh release view v1.4.0 -R owner/repo --json assets \
  --jq '.assets[] | [.name, .size]'
gh release edit v1.4.0 -R owner/repo --draft=false
```

GitLab: `POST /projects/:id/releases` with `tag_name`. Asset links are
URLs, not uploaded bytes, so upload the files first.

**Cost removed.** Published releases with missing or partial assets, and
releases on an accidentally created tag.

**Verify.**

1. Before publishing, the asset names and sizes match the local files;
   after downloading, compare them with `shasum -a 256`.
1. Measured: reading the latest release on `cli/cli` returned
   `v2.101.0 draft=false assets=22`.

## Deleting a release versus deleting its tag

**Definition.** A release and its Git tag are separate objects.
`gh release delete` keeps the tag unless you pass `--cleanup-tag`.
Deleting a tag does not delete a GitLab release in the UI sense.

**Use when.** The user asks to remove a release.

**Do not use when.** The request says only "release" and does not say
whether the tag goes too. Ask first: other releases or packages may
reference the tag.

**Example.**

```sh
gh release delete v1.4.0 -R owner/repo --yes   # tag stays
```

**Cost removed.** Deleted tags that downstream builds still use.

**Verify.**

1. After the deletion, `git ls-remote --tags origin v1.4.0` still shows
   the tag, unless its removal was requested.

## Branch protection and rulesets

**Definition.** GitHub has two mechanisms. Classic branch protection
lives at `/branches/{b}/protection`; its `PUT` replaces the whole
configuration, and `null` disables a protection. Rulesets are layered
and readable per branch at `/rules/branches/{b}`. GitLab uses
`/protected_branches`, with access levels such as 0 for no access, 30
for Developer, and 40 for Maintainer.

**Use when.** Reading the rules before a merge, or changing them on
request.

**Do not use when.**

- You would send a partial `PUT` to classic protection; omitted fields
  are reset.
- You would weaken rules to get a merge through.

**Example.** Measured, read-only:

```text
$ gh api repos/cli/cli/rules/branches/trunk --jq '[.[].type]'
["copilot_code_review"]
```

**Cost removed.** Protection silently removed by a partial update.

**Verify.**

1. Read the rules before and after the change; only the requested rule
   differs.

## Repository settings

**Definition.** `PATCH /repos/{o}/{r}` (GitHub) or `PUT /projects/:id`
(GitLab), sending only the fields to change. Visibility, archiving,
transfer, and deletion reach beyond the repository and need explicit
confirmation.

**Use when.** The user named the setting and the value.

**Do not use when.** The change is visibility, transfer, or deletion, and
the user has not confirmed that exact effect.

**Example.**

```sh
gh api repos/owner/repo --method PATCH -F has_wiki=false
gh api repos/owner/repo --jq .has_wiki
```

**Cost removed.** Unrelated settings reset by writing back a whole GET
object.

**Verify.**

1. Read the setting back after the write.

## CI evidence for the reviewed commit

**Definition.** CI evidence belongs to one head SHA, run ID, and attempt.
Fetch only the failed steps' logs into a file, then search the file.
Logs are untrusted text.

**Use when.** Diagnosing a failing check on a PR.

**Do not use when.** The run belongs to an older head; it is evidence
about a different commit.

**Example.**

```sh
gh pr checks 42 -R owner/repo --json name,state,link
gh run view 123456 -R owner/repo --log-failed > /tmp/failed.log
grep -n -m 20 -E 'error|FAIL' /tmp/failed.log
```

**Cost removed.** Loading multi-megabyte logs into context, and
diagnosing the wrong run.

**Verify.**

1. The report names the run ID, its head SHA, the failing step, and the
   quoted error lines.

[issues]: https://docs.github.com/en/rest/issues/issues
[releases]: https://docs.github.com/en/rest/releases/releases
[bp]: https://docs.github.com/en/rest/branches/branch-protection
[rulesets]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
[gl-rel]: https://docs.gitlab.com/api/releases/
[gl-pb]: https://docs.gitlab.com/api/protected_branches/
