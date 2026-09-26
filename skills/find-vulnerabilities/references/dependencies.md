# Dependencies and supply chain

Cards for known-vulnerable dependencies, package identity, and build
provenance. `verify.sh network` writes each manifest into a temporary
directory at run time, so the published skill ships no vulnerable
manifest for repository scanners to flag.

Tier: **Executed** with network on Apple M1 Max, macOS: cargo-audit 0.22.2,
bun 1.4.2 (`bun audit`), pip-audit 2.10.1 through `uvx` (not installed
locally). **Not runnable here**: osv-scanner (not installed); its card
gives the documented command, unexecuted.

## Contents

- Advisory triage by reachability
- cargo audit
- bun audit
- pip-audit
- osv-scanner
- Package identity before install
- Provenance and SBOM

## Advisory triage by reachability

**Definition.** An advisory match says a resolved package version is in
an affected range. A finding also needs the affected function or feature
in use on a path that attacker input reaches in the deployed
configuration. Report "affected version present, exploitability
unverified" separately from a traced, reachable vulnerability (CWE-1395,
Class, Allowed-with-Review).

**Use when.**

- Any audit tool reports a match.

**Do not use when.**

- You would dismiss a match because you found no call: dynamic imports,
  plugins, and transitive use hide calls; say what you searched.

**Example.**

```text
bun audit: minimist 1.2.0, GHSA-xvch-5gv4-984h (prototype pollution,
  vulnerable_versions ">=1.0.0 <1.2.6", CWE-1321)
Resolved from: bun.lock (direct dependency)
Use: rg -n "minimist" src/ -> cli.ts:4 parses process.argv only
Attacker control of argv: none in the deployed service
Status: design risk; upgrade to >=1.2.6 in the next release
```

**Cost removed.** Advisory matches reported as confirmed findings with
no use site. Count matches whose report entry has neither a use location
nor a statement of what was searched; goal 0.

**Verify.**

1. For each match, record resolved version, lockfile path, and the
   `rg` command used to find uses.
1. After the upgrade, rerun the same tool; the advisory ID is gone.

## cargo audit

**Definition.** `cargo audit` reads `Cargo.lock` and reports crates with
advisories in the RustSec Advisory Database, which it fetches
([RustSec][rustsec]). `--json` gives machine output; exit status 1 means
it found vulnerabilities (observed locally).

**Use when.**

- The repository has a `Cargo.lock`.

**Do not use when.**

- Only a `Cargo.toml` exists: generate the lockfile first
  (`cargo generate-lockfile`) so the audit sees resolved versions.

**Example.**

```console
$ cargo audit --json > audit.json; echo $?
1
$ grep -o 'RUSTSEC-[0-9]*-[0-9]*' audit.json | sort -u
RUSTSEC-2021-0003
```

The lockfile pinned `smallvec 1.6.0`.

**Cost removed.** Unaudited Rust dependencies: 1 advisory reported for
the pinned crate.

**Verify.**

1. `sh assets/examples/verify.sh network` (needs network for the
   advisory database).
1. In the target: `cargo audit` from the workspace root; record the
   advisory IDs and the database fetch date it prints.

## bun audit

**Definition.** `bun audit` reads `bun.lock` (no `node_modules` needed),
sends the package list to the npm advisory endpoint, and exits 1 when
vulnerabilities remain after filters; `--json` prints the raw response,
`--prod` limits to production dependency paths, `--audit-level` sets a
threshold ([bun audit][bun-audit]).

**Use when.**

- The project uses Bun (`bun.lock`).

**Do not use when.**

- The project uses another package manager: use that manager's lockfile
  and audit command, because resolution differs.

**Example.**

```console
$ bun install --ignore-scripts && bun audit --json > audit.json
$ echo $?
1
$ grep -o 'GHSA-[a-z0-9-]*' audit.json | sort -u
GHSA-vh95-rmgr-6w4m
GHSA-xvch-5gv4-984h
```

The JSON carries `vulnerable_versions`, `cwe`, and a CVSS vector per
advisory (`minimist 1.2.0` here).

**Cost removed.** Unaudited npm dependencies: 2 advisories reported.

**Verify.**

1. `sh assets/examples/verify.sh network`.
1. In the target: `bun audit --prod` for shipped code, then without
   `--prod` for build tooling.

## pip-audit

**Definition.** `pip-audit -r requirements.txt` checks Python
requirements against the PyPI vulnerability service by default (OSV is
selectable) and exits 1 on findings; with `--no-deps --disable-pip` it
audits exactly pinned requirements without resolving them. Its docs say
it is not a static analyzer ([pip-audit][pip-audit]).

**Use when.**

- Python projects with pinned requirements or an installed environment.

**Do not use when.**

- Requirements are unpinned and the command passes `--no-deps`: the docs
  require exact pins for that mode.

**Example.** pip-audit was not installed, so it ran through `uvx`:

```console
$ uvx pip-audit -r requirements.txt --no-deps --disable-pip \
    -f json -o audit.json; echo $?
1
$ grep -o 'PYSEC-[0-9]*-[0-9]*' audit.json | sort -u
PYSEC-2021-142
```

(`requirements.txt` pinned `pyyaml==5.3.1`.)

**Cost removed.** Unaudited Python dependencies: 1 advisory reported.

**Verify.**

1. `sh assets/examples/verify.sh network`.
1. In the target: `pip-audit` inside its environment, or `-r` for each
   pinned requirements file.

## osv-scanner

**Definition.** `osv-scanner scan -r DIR` finds lockfiles recursively and
`osv-scanner scan -L LOCKFILE` scans one, matching against the OSV
database; `--format json` gives machine output
([osv-scanner usage][osv]). One run covers many ecosystems.

**Use when.**

- A polyglot repository has several lockfile types.

**Do not use when.**

- It is not installed and cannot be (as here): use the per-ecosystem
  tools above.

**Example.** Not runnable here; documented command, unexecuted:

```sh
osv-scanner scan -r . --format json > osv.json
```

**Cost removed.** One command across lockfile types instead of one tool
per ecosystem; count lockfiles it reports scanning.

**Verify.**

1. `verify.sh network` runs it on the generated `Cargo.lock` when the
   binary exists and prints `SKIP` otherwise.

## Package identity before install

**Definition.** Before adding a dependency, confirm the exact package
name and registry from the project's official documentation or source
repository, and inspect the publisher, repository link, release history,
and install scripts. A peer-reviewed USENIX Security 2025 study observed
code models recommending nonexistent packages ([package
hallucination][usenix]); its rates do not predict any given model.

**Use when.**

- A change adds a dependency, especially one suggested by a model or a
  search result.

**Do not use when.**

- The package is already locked and approved: review its version, not
  its identity.

**Example.**

```text
Proposed: "python-jwt-tools" (from a code suggestion)
Checked:  PyPI page -> no project;  docs of the framework -> "PyJWT"
Decision: use PyJWT (already in the lockfile); drop the suggestion
```

**Cost removed.** Unverified new dependency names in the diff: count
added lockfile entries without a recorded source link; goal 0.

**Verify.**

1. For each added package, the review names the official page that
   lists it.
1. Install with scripts disabled first (`bun install --ignore-scripts`,
   `pip download` then inspect) when a package runs install hooks.

## Provenance and SBOM

**Definition.** Provenance records which source and builder produced an
artifact; SLSA 1.2 defines source and build tracks and how to verify
them ([SLSA][slsa]). An SBOM lists an artifact's components in SPDX or
CycloneDX format ([SPDX][spdx], [CycloneDX][cyclonedx]). Neither proves
the absence of vulnerabilities.

**Use when.**

- The review covers build and release: CI workflows, signing, publishing
  credentials.
- A consumer requires an SBOM for a release.

**Do not use when.**

- You would claim a SLSA level because CI exists: pick the track and
  verify its requirements against the actual builder.

**Example.**

```text
Release path: tag -> CI job "release" -> build -> sign -> publish
Check: can pull_request jobs from forks read the publish token? no
Check: provenance verified against expected repo and builder? yes
SBOM: CycloneDX generated by the build tool from the resolved artifact
```

**Cost removed.** Release credentials reachable from untrusted CI
jobs: count fork-triggered workflows that can read secrets (goal: 0).

**Verify.**

1. Read each workflow's trigger and permissions; record which can read
   release secrets.
1. Validate the SBOM with the format's official tooling before
   publishing it.

[rustsec]: https://rustsec.org/
[bun-audit]: https://bun.com/docs/pm/cli/audit
[pip-audit]: https://pypi.org/project/pip-audit/
[osv]: https://google.github.io/osv-scanner/usage/
[usenix]:
https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen
[slsa]: https://slsa.dev/spec/v1.2/
[spdx]: https://spdx.dev/use/specifications/
[cyclonedx]: https://cyclonedx.org/specification/overview/
