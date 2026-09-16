# Source index and freshness rules

This index is for source discovery and version checking. It is not a substitute
for the operational rules in `SKILL.md` and the other references. Open the
underlying source; do not treat a search snippet, generated summary, or copied
example as authority.

## Source order

1. Inspect the target repository, installed tool versions, lockfiles, generated
   relationships, and existing validation commands.
1. Use the exact product or language version's official documentation and
   source.
1. Use standards and protocol specifications for normative behavior.
1. Use issue trackers and community reports to discover failure patterns, then
   reproduce the relevant behavior locally before changing production code.

For changing products, record the page or source revision and access date in the
work product when the decision depends on it. Do not silently transfer an API or
limit from another version, fork, operating system, runtime, or hosting tier.

## Primary sources

| Source | Applicability |
| --- | --- |
| [Bun package manager](https://bun.com/docs/pm) | Current Bun package-management behavior. |
| [Bun Node.js compatibility](https://bun.com/docs/runtime/nodejs-compat) | Compatibility status for the selected Bun version; local behavior still requires testing. |
| [Bun test runner](https://bun.com/docs/test) | Current test-runner behavior and configuration. |
| [bun.com: bundler](https://bun.com/docs/bundler) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: installation](https://bun.com/docs/installation) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: install](https://bun.com/docs/pm/cli/install) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: isolated installs](https://bun.com/docs/pm/isolated-installs) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: lifecycle](https://bun.com/docs/pm/lifecycle) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: lockfile](https://bun.com/docs/pm/lockfile) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: scopes registries](https://bun.com/docs/pm/scopes-registries) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: workspaces](https://bun.com/docs/pm/workspaces) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: runtime](https://bun.com/docs/runtime) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: node api](https://bun.com/docs/runtime/node-api) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: configuration](https://bun.com/docs/test/configuration) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [bun.com: from npm install to bun install](https://bun.com/guides/install/from-npm-install-to-bun-install) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
