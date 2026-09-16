# Validate changelog structure and Semantic Versioning

## Execution and dependency

From the installed skill directory, run:

```sh
python3 -I scripts/audit_changelog.py /path/to/CHANGELOG.md --json
python3 -I scripts/audit_semver.py 1.2.3 2.0.0-rc.1 --json
python3 -I scripts/audit_semver.py --from-changelog /path/to/CHANGELOG.md
```

For `--from-tags`, run from the target Git repository and give the script's
absolute path. Git tags are local refs; the script does not fetch remote refs.

Both scripts require only Python 3.10 or later and the standard library. `-I`
isolates execution from user site packages and Python environment variables. The
bounded parser handles the heading, link, fence, indentation, comment, and
content forms in this changelog profile; it is not a general Markdown parser.
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
PYTHONDONTWRITEBYTECODE=1 python3 -I scripts/test_validators.py -v
```

Check release facts, comparisons, referenced artifacts, completeness, and public
API impact against repository evidence after automated checks. A successful
syntax audit cannot establish those properties.
