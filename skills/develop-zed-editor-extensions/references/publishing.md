# Publishing to the registry

Cards for getting an extension into, and updated in,
[zed-industries/extensions][registry]. Rules come from the publishing
docs and the registry's CI code (`src/lib/validation.js`,
`src/lib/license.js`, `src/package-extensions.js` on `main`, commit
`6743fb9`, read 2026-09-25). A registry PR is an external write, so none
of it was executed. `check_extension.py --registry` reproduces the
locally checkable rules and was Executed on all six fixtures.

## Contents

- [Extension ID and category rules](#extension-id-and-category-rules)
- [License at the extension root](#license-at-the-extension-root)
- [Registry CI checks](#registry-ci-checks)
- [Submission PR](#submission-pr)
- [Extension in a subdirectory](#extension-in-a-subdirectory)
- [Update PR](#update-pr)

## Extension ID and category rules

**Definition.** An ID must match `^[a-z0-9-]+$`, must not start with
`zed-` or end with `-zed`, and must not contain `extension`
([validation.js][validation]). The name must not start with "Zed ", end
with " Zed", or contain "extension". IDs cannot change after
publication. Expected category suffixes: `-theme`, `-icon-theme` or
`-icons`, `-snippets`, `-language-server` or `-lsp`, `-debugger`, and
`mcp-server-` or `-mcp-server` ([prerequisites][prereq]).

**Use when.**

- Before the first publication; the ID is permanent.

**Do not use when.**

- The functionality already exists in the registry. The prerequisites
  ask you to contribute to that extension instead.
- A language extension ID does not resemble the language name.

**Example.** The fixture IDs and the rule each follows:

```text
makefile            language: named after the language
marksman-lsp        language server only: -lsp suffix
lldb-dap-debugger   debugger only: -debugger suffix
mcp-server-memory   MCP only: mcp-server- prefix
ember-theme         themes only: -theme suffix
mono-icons          icon theme only: -icons suffix
```

**Cost removed.** A rejected PR, or an ID that can never be fixed: CI
fails on the pattern rules and renames are impossible. The checker
reports each violation (unit test `test_registry_rejects_bad_identity`,
Executed).

**Verify.**

1. `check_extension.py --registry EXT_DIR` prints `0 errors`. Executed
   on six fixtures.
1. Before opening the PR, search a registry clone for an extension with
   the same purpose: `rg -n '^\[' extensions.toml`.

## License at the extension root

**Definition.** Since 2025-10-01 every extension needs, in the extension
directory itself, a file whose name without extension starts with
`license` or `licence` (case-insensitive). In a monorepo that is the
subdirectory, not the repository root. The file must contain one of:
Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-4.0, GPLv3, LGPLv3, MIT,
Unlicense, or zlib. CI matches required phrases after collapsing
whitespace ([license docs][license], [license.js][license-js]).

**Use when.**

- Every registry submission and update.

**Do not use when.**

- Relicensing a project without the owner's authority. Only the
  extension code needs the license, not downloaded servers.

**Example.** Each fixture carries the standard MIT text in `LICENSE`.
The phrases CI requires for MIT:

```text
Copyright
Permission is hereby granted, free of charge, to any person obtaining a copy
The above copyright notice and this permission notice shall be included in all
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
```

**Cost removed.** A certain CI failure: "No license was found" or "No
valid license found". `check_extension.py --registry` checks the file
name and all MIT phrases; for other licenses it checks a subset, and
registry CI stays the authority.

**Verify.**

1. `check_extension.py --registry` prints no license error. Executed.
1. The unit test `test_registry_requires_license` fails a fixture
   without `LICENSE`. Executed.

## Registry CI checks

**Definition.** For each changed extension, registry CI checks
`extensions.toml`, the submodule URLs (`https://` only), and the
`extension.toml` ID and version, then runs Zed's `zed-extension`
packager with `--source-dir`, `--output-dir`, and `--scratch-dir`
([package-extensions.js][package-js]). The packager builds in release
mode; requires a name, a description longer than the name, an author,
and a repository URL; rejects themes or icon themes mixed with other
features, slash commands, and language model providers; compiles every
query; rejects unknown files in language directories; and parses
themes, snippets, and debug schemas ([CLI][cli-rs]).

**Use when.**

- Right before opening the PR: reproduce as much as possible locally.

**Do not use when.**

- Replacing the test in Zed with local checks. The prerequisites require
  a manual test at the submitted commit.
- Building `zed-extension` from the Zed workspace to check a small
  change. The local checkers, `tree-sitter query`, and `cargo
  build --release --target wasm32-wasip2` cover the same rules; the
  only difference is that the CLI compiles queries natively while Zed
  uses the wasm grammar.

**Example.** The local equivalent, run for every fixture by `verify.sh`:

```sh
python3 scripts/check_extension.py --registry EXT_DIR
python3 scripts/check_queries.py EXT_DIR/languages/NAME \
  --node-types GRAMMAR/src/node-types.json
python3 scripts/check_theme.py EXT_DIR/themes/T.json --schema S.json
cargo build --release --target wasm32-wasip2
```

**Cost removed.** One CI round trip per rule. The FAQ says most
submissions get first feedback within a few weeks ([FAQ][faq]), so
every failure found locally saves one of those cycles.

**Verify.**

1. `sh assets/examples/verify.sh` ends with `35 checks passed` when a
   `tree-sitter` CLI is available; without one it prints a SKIP line
   and passes 26 checks. Executed with tree-sitter 0.27.0.
1. After the PR opens, the registry CI job is green (Not runnable
   here).

## Submission PR

**Definition.** Fork `zed-industries/extensions`, preferably to a
personal account so staff can push fixes. Add the extension as a git
submodule at `extensions/<id>` with a public HTTPS URL and a commit that
is on a branch. In `extensions.toml`, add `[<id>] submodule =
"extensions/<id>"` and `version`, equal to `extension.toml`'s version at
that commit. Run `pnpm
sort-extensions`. One extension per PR, at most three open PRs per
author, and a PR closes after 3 weeks without a reply to feedback
([publishing guide][guide]). A merge triggers packaging and
publication.

**Use when.**

- The extension passes the checks above and you tested it manually at
  the submodule commit, as the prerequisites require.

**Do not use when.**

- Running `bun run sort-extensions` or `npm run`. The registry uses
  pnpm (`pnpm-lock.yaml`; [its justfile][registry-just] has
  `just sort-extensions` call `pnpm sort-extensions`).
- An SSH submodule URL (`git@github.com:`). CI requires `https://`.

**Example.** Not runnable here: it writes to a GitHub fork.

```sh
git clone https://github.com/<you>/extensions
cd extensions
git submodule init
git submodule update
git submodule add https://github.com/<you>/zed-makefile.git \
  extensions/makefile
git add extensions/makefile
```

```toml
[makefile]
submodule = "extensions/makefile"
version = "0.1.0"
```

```sh
pnpm sort-extensions
git commit -am "Add makefile extension"
```

**Cost removed.** A closed PR: the docs say PRs that break the rules
close without feedback.

**Verify.**

1. `git -C extensions/makefile branch -r --contains HEAD` is not empty,
   so the commit is on a branch.
1. `git config -f .gitmodules submodule.extensions/makefile.url` starts
   with `https://`.

## Extension in a subdirectory

**Definition.** `path` in the `extensions.toml` entry points inside the
submodule when the repository holds more than the extension. CI joins
the submodule path and `path` to find `extension.toml` and the license
([package-extensions.js][package-js]).

**Use when.**

- The extension shares a repository with a language server or grammar.

**Do not use when.**

- The license is only at the repository root. Put it inside the `path`
  directory, as a copy or a symlink.

**Example.**

```toml
[my-extension]
submodule = "extensions/my-extension"
path = "packages/zed"
version = "0.0.1"
```

**Cost removed.** A separate repository just for the extension.

**Verify.**

1. `ls extensions/my-extension/packages/zed/extension.toml
   extensions/my-extension/packages/zed/LICENSE*` lists both files.
1. `check_extension.py --registry
   extensions/my-extension/packages/zed` prints `0 errors`.

## Update PR

**Definition.** Move the submodule to the new commit
(`git submodule update --remote extensions/<id>`) and set `version` in
`extensions.toml` to the new `extension.toml` version. The version must
not decrease, the ID must not change, and the same PR rules apply
([updating][updating], [validation.js][validation]).

**Use when.**

- Every release after the first.

**Do not use when.**

- `extension.toml` was not bumped. CI compares the packaged version with
  the registry entry and fails with "Incorrect version".

**Example.** Not runnable here.

```sh
git submodule update --remote extensions/makefile
git -C extensions/makefile log -1 --format=%H
sed -n 's/^version = //p' extensions/makefile/extension.toml
# set the same version under [makefile] in extensions.toml
```

**Cost removed.** A failed update PR, for one command that compares the
two version strings.

**Verify.**

1. The version in `extensions.toml` equals `extension.toml` at the
   submodule commit.
1. The new version is greater than the old one under semver.

[registry]: https://github.com/zed-industries/extensions
[registry-just]: https://github.com/zed-industries/extensions/blob/main/justfile
[validation]: https://github.com/zed-industries/extensions/blob/main/src/lib/validation.js
[license-js]: https://github.com/zed-industries/extensions/blob/main/src/lib/license.js
[package-js]: https://github.com/zed-industries/extensions/blob/main/src/package-extensions.js
[guide]: https://zed.dev/docs/extensions/publishing/publishing-guide
[prereq]: https://zed.dev/docs/extensions/publishing/prerequisites
[license]: https://zed.dev/docs/extensions/publishing/license-requirements
[updating]: https://zed.dev/docs/extensions/publishing/updating-and-maintenance
[faq]: https://zed.dev/docs/extensions/publishing/faq
[cli-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_cli/src/main.rs
