# Bun migration boundary and execution evaluation

Evaluated 2026-09-11. This accepts the migration capability, not Bun performance
or all remaining repository work.

## Boundary decision

Use `migrate-bun-toolchain` for Bun adoption and existing-project Bun version
transitions. The inherited `migrate-node-to-bun` rename excluded version-only
upgrades that the original `bun-migration` covered. That scope loss was not
justified by different expertise or validation: both need version selection,
pins, lockfile compatibility, and affected-consumer checks. No extra upgrade
micro-skill is added. Catalog count remains 40.

Eight inherited references become two substantive documents without intermediate
routers. Removed the undefined `normalize` test example rather than claiming
that a trivial assertion validates migration. Guidance separates installer,
runtime, test-runner, and bundler changes; adoption does not require rewriting
application code or adding setup/configuration.

Existing catalog routing reports retain their historical names and judgments.
This evaluation supersedes the Bun-only coverage question there. The original
`bun-migration` files are retired in the same commit; no internal skill links
still use either old name.

## Current sources and concrete corrections

Opened the current official documentation for
[installation](https://bun.com/docs/installation),
[lockfiles](https://bun.com/docs/pm/lockfile),
[lifecycle trust](https://bun.com/docs/pm/lifecycle),
[registries](https://bun.com/docs/pm/scopes-registries),
[isolated linking](https://bun.com/docs/pm/isolated-installs),
[runtime commands](https://bun.com/docs/runtime),
[test configuration](https://bun.com/docs/test/configuration), and
[bundling](https://bun.com/docs/bundler). Used installed `bun install --help`
for actual command flags. Source-sensitive guidance records the inspection date.

Installed current runtime is Bun `1.4.2+744846f84`. Downloaded the official
[1.1.45 release binary](https://github.com/oven-sh/bun/releases/tag/bun-v1.1.45)
for a real binary-lockfile transition; its revision is `196621f2`.

Observed conversion behavior improves the guidance: Bun 1.4.2 removes
`bun.lockb` when writing the text lockfile through the documented conversion
command. An initial attempt to copy the binary afterward failed. A separate
controlled repeat showed frozen installation retains it, while conversion
removes it. Guidance now requires retaining the original before conversion,
especially when older consumers still need binary format.

The isolated-linker documentation also distinguishes store fallback visibility
from strict dependency enforcement. Guidance no longer implies that choosing an
isolated layout alone proves undeclared dependencies are inaccessible.

## Existing Bun version transition

A disposable release-policy fixture uses the maintained `semver@7.7.2` library
and an actual Bun test: a stable compatible release is accepted, while a
prerelease and next-major release are rejected. No SemVer parser was invented.

- Bun 1.1.45 generated a binary lockfile and passed the behavior test.
- Bun 1.4.2 accepted a frozen install using that binary lockfile.
- The documented `--save-text-lockfile --frozen-lockfile --lockfile-only`
  conversion generated `bun.lock`. The old readable lock and new text lock
  preserve version 7.7.2 and the same SHA-512 registry integrity.
- Updated the fixture's Bun pin without changing dependency constraints or its
  test runner. A fresh copy without `node_modules` installed the text lock with
  Bun 1.4.2 and passed `bun run test`.
- Changing only the copied manifest to require 7.7.1 made the frozen install
  exit 1 with a lockfile-change error. Success was not obtained by regenerating
  the lockfile or disabling the frozen check.

A separate local dependency fixture ran a harmless postinstall that writes a
build marker. With omitted trust and with an empty trust list, installation
blocked the script and the marker was absent. Explicitly trusting that local
package produced the marker. These three native runs validate local-source trust
behavior, not every npm default-trust-list entry.

## Independent package-manager adoption

A fresh-context evaluator received a raw npm-installed report-export CLI and the
request to move installation to Bun 1.4.2 while retaining Node and `node:test`.
The CLI uses `csv-stringify@6.6.0`, not handwritten CSV escaping. Its tests run
the actual subprocess and assert Unicode/quote/newline output bytes and a
nonzero malformed-JSON exit with no CSV header emitted.

The evaluator generated a Bun lock, added the exact Bun pin, verified
resolution, and removed the npm lock only afterward. Both Node tests passed
through direct `node --test` and `bun run test`; the latter visibly invoked
`node --test`. The application and test bytes are unchanged. Integration
compared manifests, source/test bytes, package identity, and SHA-512 integrity
with the original npm v3 lock. Only the requested installer/pin artifacts
changed.

Seven final-name routing prompts were evaluated against the full catalog:

- Direct: move npm installation to Bun 1.4.2, retaining Node and node:test →
  `migrate-bun-toolchain`.
- Paraphrase: switch the dependency installer without replacing Node scripts →
  `migrate-bun-toolchain`.
- Incomplete: “Upgrade our Bun setup to 1.4.2.” → select the migration skill,
  then inventory affected consumers.
- Adjacent: profile Bun server allocations → `optimize-bun-code`.
- Unrelated: create a GitHub pull request → `manage-pull-requests`.
- Ambiguous surface: “Use Bun for this project.” → select migration guidance,
  establish the requested surface before editing.
- Composition: migrate npm installation and its GitHub Actions installer →
  migration plus `develop-ci-pipelines`.

These are reviewer routing judgments, not client-loader telemetry.

## Gates and limits

Both skill validators, documented-field YAML checks, Markdown, relative links,
old-name search, and `git diff --check` pass. Tests used actual macOS ARM64
Bun/Node processes and disposable files, not mocked package managers. Node was
26.8.2 and npm 11.19.1. No downloaded binaries, lockfiles, or test caches enter
the repository skill.

No claim is made for Windows/Linux installs, private registries, native addons,
workspace migrations, Jest conversion, browser output, container deployment, or
runtime-switch compatibility. Those paths require task-specific evidence. The
fixture is an evaluation artifact, not a new published CSV product or a
requirement to add a starter to every migration skill.
