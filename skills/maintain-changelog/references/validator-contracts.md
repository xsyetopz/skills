# Validator contracts

## Execution and dependency

From the installed skill directory, run:

```sh
uv run scripts/audit_changelog.py /path/to/CHANGELOG.md --json
uv run scripts/audit_semver.py 1.2.3 2.0.0-rc.1 --json
uv run scripts/audit_semver.py --from-changelog /path/to/CHANGELOG.md
```

For `--from-tags`, run from the target Git repository and give the script's
absolute path. Git tags are local refs; the script does not fetch remote refs.

Both scripts declare Python 3.10+ and `markdown-it-py==4.2.0` using
[inline script metadata](https://docs.astral.sh/uv/guides/scripts/). `uv run`
resolves the declared environment; it does not add dependencies to the target
project. An existing Python environment with this dependency can run them with
`python` instead. Initial dependency installation can require network access.

The maintained
[CommonMark parser](https://markdown-it-py.readthedocs.io/en/latest/using.html)
handles headings, links, fences, indentation, and comments. The scripts apply a
small changelog profile to parsed sections instead of implementing Markdown.
SemVer syntax uses the specification's published regex with ASCII digits and a
whole-string match, not a custom precedence implementation.

## Changelog profile

Top-level H2 headings identify releases. Their displayed label is `Unreleased`
or a SemVer version followed by a spaced hyphen, `YYYY-MM-DD`, and optionally a
spaced `[YANKED]`. Linked, bracketed, and plain version labels are accepted,
including Setext headings. Headings inside code, HTML comments, blockquotes, and
lists are not release sections. H3 headings identify change categories. This is
a deliberately bounded profile, not validation of every possible changelog
convention.

Errors report invalid versions/dates, duplicate release/category headings,
misplaced Unreleased, orphan/unknown/empty categories, empty released sections,
and missing release sections. Empty Unreleased is allowed. Prose and nested
subsections can contain entries; headings and comments alone cannot. Missing
Unreleased and a different title are warnings. These severity choices are this
checker's profile, not normative requirements from Keep a Changelog.

The JSON object contains `path`, `findings`, and `versions`. Each finding has
`severity`, `rule`, `location`, and `message`. Errors exit 1; warnings alone
exit 0, in both output modes. Argument syntax errors exit 2. File-reading errors
are reported without tracebacks. The script neither edits files nor requests
links.

## SemVer checker

Direct versions must be bare SemVer. Only `--from-tags` accepts a leading `v`
and reports it as a tag wrapper. The tag selector checks names beginning with a
numeric major/minor pair, optionally prefixed by `v`; unrelated names are not
release-version candidates. Git's tag sort is not proof of SemVer precedence.

`--from-changelog` checks labels from all top-level H2 headings except
Unreleased, including malformed labels. It does not audit release dates or
categories. Use the changelog checker for that profile. No selected versions,
invalid versions, or source failures exit 1; argument errors exit 2.

JSON output is a list of per-version records. Numeric components are decimal
strings so unbounded SemVer integers do not overflow a consumer's number type or
Python's string-to-integer conversion limit. Prerelease and build metadata are
strings or null. Source errors are sent to stderr and do not produce a partial
JSON result.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --with markdown-it-py==4.2.0 \
  python -m unittest discover -s scripts -v
```

Check release facts, comparisons, referenced artifacts, completeness, and public
API impact against repository evidence after automated checks. A green syntax
audit cannot establish those properties.
