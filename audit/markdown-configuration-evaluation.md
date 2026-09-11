# Markdown configuration discovery correction

Evaluated 2026-09-12. This finding corrects earlier validation claims; it does
not establish full-suite completion.

## Root cause and impact

The inherited `.markdownlint-cli2.json` basename is not automatically discovered
by markdownlint-cli2 0.23.2. The fallback runner therefore used defaults rather
than that file. Its printed success did not prove compliance with the intended
repository policy. Earlier audit statements that Markdown checks passed remain
records of command results, not proof that the configured strict policy ran.

The [official CLI2 documentation][cli2] and actual `--help` list the supported
CLI2 basename `.markdownlint-cli2.jsonc` instead. A controlled probe confirms
the difference: a Markdown asterisk list passes with the unsupported `.json`
file, while the identical asset named `.jsonc` produces its intended MD004
violation. The real runner test asserts the diagnostic, not just file existence.

Restored the original committed repository configuration, byte-for-byte, at root
`.markdownlint-cli2.jsonc`. This replaces the inherited unsupported root file
and moves the original `skills/.markdownlint-cli2.jsonc` scope to the root. No
rule was disabled: code blocks, tables, and headings remain subject to strict
80-column MD013. The less restrictive optional skill asset is not substituted
for repository policy.

The first correct full scan found **123 diagnostics across 80 of 243 files**.
These were real formatting failures, including previously accepted areas. The
subsequent correction below resolves them without suppressions or warnings. The
initial output is retained temporarily at
`/tmp/skills-strict-markdown-baseline.log`.

## Helper and skill repairs

- Renamed the bundled asset and installer output to supported `.jsonc`.
- Preserved both documented CLI2 and ordinary `.markdownlint.*` root
  configurations rather than checking CLI2 names alone.
- Refused to hide an existing unsupported `.markdownlint-cli2.json` behind a new
  configuration. The diagnostic requires deliberate review of its name.
- Preserved dangling configuration symlinks rather than following or replacing
  them. Applied CDPATH isolation to both script and target-directory resolution.
- Reduced the entrypoint to the actual opt-in workflow. Existing project tools
  and configuration take precedence; custom command-selected configuration must
  be inspected before installing defaults. No custom config parser was added.
- Removed duplicated rule prose and the padded-table example that contradicted
  the bundled compact-table policy. Formatter/linter conflicts now require a
  policy decision rather than endless alternating output.

The installer intentionally checks the chosen root's recognized filenames. It is
not a substitute for inspecting command arguments, nested overrides, or non-CLI2
tools. The fallback runner remains optional and pinned; it does not force a
project to adopt Bun or replace its existing command.

## Validation

Five stdlib unittest cases run the actual helper. They cover discovered policy
behavior through the real CLI, preservation of existing rule and CLI configs,
unsupported-name refusal, and dangling-symlink preservation. Paths contain
spaces and CDPATH is set. All five pass. ShellCheck, Bash syntax, shfmt, Ruff,
and Python formatting checks pass without suppressions.

Both explicit-only skill packages pass official skills-ref and the bundled quick
validator. Their changed entrypoints pass the restored strict Markdown
configuration. `interrogate-plan` remains a short instruction-only workflow; it
adds no scripts, scaffolding, or implementation permission. Earlier catalog
cases document its explicit-only routing. Its metadata and body now agree on
that requirement, as does the formatting package.

## Full-corpus formatting correction

The repeat baseline contained 244 files and the same 123 diagnostics. Converted
long inline links on diagnosed lines in 80 files to CommonMark reference links.
markdown-it-py's CommonMark renderer produced identical before/after HTML for
every converted file. Prettier then reflowed one remaining overlong prose line.

The [official MD013 rule documentation][md013] exempts reference definitions,
including in strict mode. This uses ordinary Markdown syntax, not a rule
suppression or a changed configuration. URLs and rendered labels are preserved.

The full `skills/**/*.md` and `audit/*.md` scan now passes: **244 files, zero
diagnostics**. It also passes after the manual-invocation contract updates. This
scope excludes the unintegrated root guidance and source-material intake; it
does not establish final all-repository validation or technical acceptance of
pending domain packages.

This result does not claim that a JSON schema validates behavior or that every
agent host enforces OpenAI-specific invocation metadata.

[cli2]: https://github.com/DavidAnson/markdownlint-cli2#configuration
[md013]: https://github.com/DavidAnson/markdownlint/blob/main/doc/md013.md
