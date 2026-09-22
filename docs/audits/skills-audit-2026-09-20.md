# Skills directory audit and rewrite

Date: September 20, 2026. Input: the supplied
`xsyetopz-skills.zip`, archived .NET performance skill, four
ecosystem CSV indexes, and language-layout template bundle.

## Delivered scope

All **44 existing skill directories and `name` values are
preserved**. Every `SKILL.md` and native default prompt has
been rewritten. Existing native invocation policies are
unchanged, including explicit-only phase-gated coordination.
The original repository's non-skill files remain
byte-identical; no root tooling, dependency, build, lint, or
workflow configuration was replaced. Audit evidence lives
here, outside the published skills.

The `skills/` tree contains **843 files**, up from 381; 478
files were added, 90 existing files modified, and 16
generated cache files removed. Actual file content grew from
1,067,548 to 3,002,979 bytes. These counts describe coverage
and packaging, not measured agent effectiveness.

All entrypoint bodies contain 49–71 lines, within the
repository's 220-line policy. Depth is in linked references,
executable examples, source skeletons, worksheets, scripts
and evaluation fixtures rather than an enormous activation
prompt. The package does not claim that any finite
collection contains every possible relevant resource.

## Audit findings and disposition

| Finding in supplied material | Disposition |
| --- | --- |
| Nine optimization skills had no assets or scripts, leaving benchmark/oracle construction to the agent. | Added language-specific runnable kernels and behavior checks, appropriate benchmark integration templates, experiment records and detailed profiling/decision guidance. |
| Existing descriptions and workflows did not consistently separate task scope, target evidence, unsafe changes, resource use and completion claims. | Rewrote all 44 entrypoints around the actual task, responsible boundary, selective resources and observable completion. Added neighboring-task discovery negatives. |
| C optimization assumed a preferred build tool rather than the actual project toolchain. | The new workflow records and preserves the real compiler/build/target; the isolated teaching recipe does not replace project tooling. |
| Kotlin guidance could suggest that Sequence itself means single-pass consumption. | New guidance distinguishes recomputation, repeatable sequences and explicitly constrained one-shot sequences; the fixture executes both cases. |
| Python free-threading guidance needed version/build/runtime distinctions. | Added optional-build and runtime-GIL applicability, extension effects and separate experiments instead of assuming that a language version proves parallel execution. |
| Hook entrypoint mentioned a nonexistent `assets/opencode/` location. | Resource routing uses the actual supplied hook assets, including the versioned OpenCode resource; host loading remains distinct from payload parsing. |
| Python bytecode and Gradle internal state were included as published assets. | Removed eight `.pyc` files and eight Gradle cache/lock/state files. The input archive's packaging metadata is not reproduced as skill content. |
| Existing JavaScript timer measured fixed-order batches with an uninformative XOR sink. | Added bounded CLI validation, independent oracle, observable accumulated output, AB/BA order, environment and raw samples; explicitly classified as exploratory, not a calibrated regression gate. |
| Archived C# material mixed valuable low-level topics with blanket unsafe/GC/overflow or tuning choices and overconfident lexical scanning. | Adapted its optimization ladder and native lifetime topics. Did not carry over unsafe defaults, unchecked arithmetic, universal GC/PGO prescriptions, or scanner output as proof. |
| No complete task/discovery evaluation material existed across the catalog. | Added 132 synthetic task cases, 453 assertions and 176 discovery cases, with a tested fixture checker and a fresh-context comparison protocol. They are inputs, not reported agent evaluation results. |

This audit inspected every entrypoint and package inventory,
the governing repository instructions, existing
helpers/examples relevant to their changed contracts, the
supplied archive and templates, and primary
authoring/runtime sources. Existing specialist references
were retained rather than discarded to manufacture a
rewrite. Not every historical external reference, platform
API, or remote link was independently revalidated.

## Authoring and research basis

The
[Agent Skills specification](https://agentskills.io/specification)
permits files and directories beyond the conventional
`scripts/`, `references/`, and `assets/`. It has no stated
package-wide material cap. Its recommendations for short
activation instructions are different from this repository's
220-line body rule. The rewrite therefore adds substantial
conditionally loaded material rather than deleting useful
depth or filling every entrypoint with catalogs.

The
Agentskills evaluation guide
provides the task-case envelope and controlled
old/no-skill/with-skill comparison pattern. The local
trigger envelope and assertion checker are catalog
conventions, not additional Agent Skills specification
requirements. Parser success, compiled examples and fixture
integrity do not establish that an agent used the skill
effectively.

The
Cloudflare agent-skills documentation
separates activation, resource access and opt-in script
execution. Native compilers, profilers, writable workspaces,
network access and host integration are not conferred by a
skill merely loading. The
[Cloudflare skills collection](https://github.com/cloudflare/skills)
and
Cloudflare web-perf source
provided a concrete example of tool prerequisites and
observation-to-decision routing; its installation commands
and thresholds were not copied as universal project policy.

Practitioner evidence is recorded with limits.
Claude plug-ins issue 1357
reports a trigger harness affected by other skills, early
trace termination and a synthetic identity.
[Agent Skills issue 97](https://github.com/agentskills/agentskills/issues/97)
reports incomplete reference reads and cached-context
omissions. These are first-person reports, not controlled
prevalence estimates or proof of present bugs in every host.
The evaluation protocol consequently distinguishes harness
failure from non-activation and tests the actual catalog
identity and full trace.

Language-specific additions cite primary documentation in
their respective playbooks, including Go's `B.Loop` version
boundary, Python free-threading, JMH, Google Benchmark,
Cargo profiles and TypeScript compiler-performance guidance.
Supplied catalogs remain user-provided snapshots rather than
a substitute for version-matched documentation.

## Optimization material

Every optimization skill now has a measurement protocol,
target-specific decision and rejection criteria,
semantic/ownership obligations, worked counterexample,
experiment worksheet, behavior/evaluation fixtures and
example/harness instructions. The measurement protocol
distinguishes CPU, allocation and retained memory,
throughput and tail latency, startup/build cost,
calibration, process repetitions, uncertainty, equivalent
work and end-to-end impact. It does not prescribe an
invented universal performance threshold.

| Language key | Material and technical focus |
| --- | --- |
| `c` | C11 kernels, byte-safe delimiter oracle, scratch ownership, Google Benchmark integration and UB/aliasing/vectorization guidance. |
| `cpp` | C++17 materialization/fusion kernels, value/ownership tests, Google Benchmark integration and iterator/layout/allocator tradeoffs. |
| `csharp` | Existing .NET 10/C# 14 examples plus BDN pooling, native-lifetime worksheet, archived hot-path ideas, strict lexical/MSBuild inspector and .NET catalog. |
| `go` | Native testing benchmarks, independent/ownership oracles, version-gated B.Loop template, allocation/race guidance and Go catalog. |
| `java` | Java kernels and independent checks, JMH template, JIT/fork/GC/profile attribution and representation/concurrency tradeoffs. |
| `javascript` | Retained eight comparison pairs; strengthened Node timing CLI, AB/BA raw samples, independent oracle and tested misuse rejection. |
| `kotlin` | Kotlin/JVM kernels, repeatable versus one-shot Sequence checks, JMH template and boxing/coroutine/backend distinctions. |
| `python` | Independent kernels/tests, pyperf integration with propagated worker arguments, ownership/laziness and free-threading applicability. |
| `rust` | Retained Cargo experiments and checked arithmetic; optional Criterion integration, ownership/layout/unsafe proof guidance and Rust catalog. |
| `scala` | Scala 2.13/3 JVM kernels, view recomputation check, JMH integration and strict/view/lazy collection tradeoffs. |
| `swift` | Optimized Swift kernels, copy-on-write ownership tests, Apple XCTest template and ARC/exclusivity/bridging guidance. |
| `typescript` | Runtime kernels plus strict/negative type tests, cold/warm compiler experiment sheet, version separation and TS/Bun catalog. |

The native examples use independent expected outputs, not
only agreement between two implementations. They cover
empty/negative/mixed/boundary values and relevant ownership,
laziness or type-contract cases. Harness templates use the
project's existing dependency and build policy; they do not
silently add JMH, Criterion, Google Benchmark, pyperf or
another runtime. Runtime-specific integrations are clearly
separated from source-layout skeletons and from actually
executable examples.

### C# archive adaptation

`optimize-csharp-code/references/advanced-hotpaths-and-bindings.md`
turns useful archived ideas into conditional escalation:
attributable allocation/abstraction costs, representation,
borrowing, pooling, SIMD, deployment experiments and native
bindings. The native-ownership worksheet records allocators,
logical versus physical lengths, stable addresses, handles,
callbacks, async completion, cancellation and release
responsibility. A comment is not proof of lifetime safety.

The new read-only inspector reports lexical leads and
unevaluated MSBuild declarations, preserves conditions and
duplicate declarations, reports malformed XML and
bounded-input errors, and does not infer effective defaults
from absent properties. Ten tests cover those boundaries.
The existing stricter benchmark CSV comparator and its tests
are retained; the archived weaker comparator was not
substituted. The .NET 10/C# 14 example configuration remains
the actual supplied target, not an upgraded or downgraded
replacement.

### Supplied ecosystem indexes

The four UTF-8 CSV indexes retain **1,577 package records**:
464 .NET, 343 Go, 365 Rust, and 405 TypeScript. Each has the
same eight columns: `Section`, `Name`, `Description`, `Use
Case`, `Status`, `Recommendation`, `Alternatives`, and
`Evidence`. Sections group related entries; multiple
alternatives use semicolons. Snapshot metadata, hashes,
technical classifications, provenance manifests, and
JSONL-specific query helpers are intentionally absent.

| File | Data rows |
| --- | --- |
| `dotnet-ecosystem-index.csv` | 464 |
| `go-ecosystem-index.csv` | 343 |
| `rust-ecosystem-index.csv` | 365 |
| `typescript-ecosystem-index.csv` | 405 |

Maintenance labels and recommendation guidance remain
attributed to the supplied catalog context, not independently
certified as current facts or converted into automatic edits.
The repository asset validator parses CSV files with the
standard-library reader and checks that every row has the
header's field count.

### Supplied source-file layouts

`design-system-architecture/assets/source-layouts/`
preserves all **30 supplied files**: **17 source skeletons,
11 Mermaid layout diagrams and 2 accompanying documents**.
Source skeleton filenames gain `.template` so placeholder
code is not accidentally compiled, imported or treated as a
runnable test. Their contents and diagrams are
byte-identical, with an original-to-packaged path map and
hashes. A usage guide explains placeholder replacement,
language-specific visibility/import decisions and adaptation
to the actual repository rather than imposition of a new
file architecture.

## Per-skill changes

Every row also includes a rewritten entrypoint/default
prompt, tailored detailed workflow, task workbook or
experiment record, and three task cases plus discovery
tests. File counts include retained useful resources and the
removed generated files in the original count.

| Preserved skill identity | Files before → after | Substantive focus |
| --- | --- | --- |
| `analyze-scientific-papers` | 10 → 17 | Claim-to-source tracing, study design, confounding, uncertainty and reproduction evidence; retained metadata lookup with tests. |
| `apply-pep20-to-codebases` | 8 → 15 | Translate PEP 20 into concrete behavior-preserving decisions; avoid stylistic dogma and unrelated language rewrites. |
| `apply-semver-versioning` | 7 → 15 | Public compatibility surface, prerelease/build precedence, release classification and version-validation evidence. |
| `build-and-debug-duckstation` | 11 → 19 | Exact checkout/build/configuration, reproducible emulator state, subsystem isolation and baseline-versus-candidate evidence. |
| `build-and-debug-pcsx2` | 11 → 19 | PCSX2 build/configuration and emulation boundary; deterministic reproduction, subsystem diagnosis and correct host limits. |
| `configure-ci-cd-pipelines` | 10 → 18 | Event trust, untrusted contributions, permission scope, cache/artifact identity and deployment authority. |
| `coordinate-phase-gated-subagents` | 16 → 24 | Explicit selection retained; work ownership, disjoint delegation, inspected child artifacts and evidence-backed phase gates. |
| `create-agent-hooks` | 24 → 32 | Native payload/transport/enforcement contracts, blocking versus observational hooks, lifecycle and host-loading checks. |
| `create-agent-skills` | 11 → 23 | Complete-package audit, discovery boundaries, resource organization, host portability, practitioner reports and tested eval-fixture checker. |
| `define-requirements` | 4 → 12 | Observable behavior, negative/failure conditions, compatibility, acceptance evidence and unresolved product decisions. |
| `design-system-architecture` | 14 → 55 | Component/data/ownership boundaries, alternatives and quality attributes; supplied source-layout bundle and adaptation guide. |
| `develop-eclipse-ide-plugins` | 19 → 27 | Bundle/extension registration, workspace jobs, UI execution, resource ownership, packaging and target-host evidence. |
| `develop-intellij-platform-plugins` | 20 → 20 | PSI/VFS validity, command/read/write actions, disposables, indexing, supported IDE builds and real-host tests. |
| `develop-neovim-plugins` | 10 → 18 | Buffer/window lifetime, async stale-state checks, reload/teardown, native APIs and actual Neovim host behavior. |
| `develop-sublime-text-plugins` | 11 → 19 | View validity, TextCommand edit/undo ownership, thread boundaries, lifecycle and explicit host-only test limits. |
| `develop-vscode-extensions` | 12 → 20 | Extension activation/disposal, cancellation, async document identity, contribution registration and packaged-host behavior. |
| `develop-zed-editor-extensions` | 13 → 21 | Actual extension API capabilities, language-server integration, execution/runtime boundaries and package verification. |
| `diagnose-software-failures` | 5 → 13 | Earliest incorrect state, causal hypotheses and discriminating experiments rather than symptom suppression. |
| `document-codebases` | 8 → 16 | Implementation/test-grounded API and operational documentation, source drift and verification by the intended reader. |
| `find-implementation-plan-flaws` | 4 → 12 | Dependencies, sequencing, unsupported assumptions, missing acceptance checks and smallest necessary plan corrections. |
| `find-regression-commits` | 7 → 14 | Verified good/bad revisions, oracle exit semantics, skipped/unbuildable revisions and safe worktree isolation. |
| `find-vulnerabilities` | 6 → 14 | Authorized trust-boundary analysis, reachable source-to-sink evidence, safe fixtures and root-boundary remediation. |
| `manage-git-changes` | 6 → 14 | Working tree/index separation, exact staged intent, semantic slices, user work preservation and observed commit state. |
| `manage-git-hosting` | 10 → 18 | Repository/PR identity, hosted reviews/checks, permission-sensitive writes and verification of actual remote state. |
| `migrate-js-tooling-to-bun` | 4 → 12 | Separate package manager, script runner and application runtime; lockfiles, CI parity and preserved runtime contracts. |
| `optimize-c-code` | 3 → 18 | C11 kernels, byte-safe delimiter oracle, scratch ownership, Google Benchmark integration and UB/aliasing/vectorization guidance. |
| `optimize-cpp-code` | 3 → 18 | C++17 materialization/fusion kernels, value/ownership tests, Google Benchmark integration and iterator/layout/allocator tradeoffs. |
| `optimize-csharp-code` | 18 → 37 | Existing .NET 10/C# 14 examples plus BDN pooling, native-lifetime worksheet, archived hot-path ideas, strict lexical/MSBuild inspector and .NET catalog. |
| `optimize-go-code` | 3 → 23 | Native testing benchmarks, independent/ownership oracles, version-gated B.Loop template, allocation/race guidance and Go catalog. |
| `optimize-java-code` | 3 → 17 | Java kernels and independent checks, JMH template, JIT/fork/GC/profile attribution and representation/concurrency tradeoffs. |
| `optimize-javascript-code` | 9 → 20 | Retained eight comparison pairs; strengthened Node timing CLI, AB/BA raw samples, independent oracle and tested misuse rejection. |
| `optimize-kotlin-code` | 3 → 16 | Kotlin/JVM kernels, repeatable versus one-shot Sequence checks, JMH template and boxing/coroutine/backend distinctions. |
| `optimize-python-code` | 3 → 17 | Independent kernels/tests, pyperf integration with propagated worker arguments, ownership/laziness and free-threading applicability. |
| `optimize-rust-code` | 10 → 26 | Retained Cargo experiments and checked arithmetic; optional Criterion integration, ownership/layout/unsafe proof guidance and Rust catalog. |
| `optimize-scala-code` | 3 → 16 | Scala 2.13/3 JVM kernels, view recomputation check, JMH integration and strict/view/lazy collection tradeoffs. |
| `optimize-swift-code` | 3 → 16 | Optimized Swift kernels, copy-on-write ownership tests, Apple XCTest template and ARC/exclusivity/bridging guidance. |
| `optimize-typescript-code` | 3 → 24 | Runtime kernels plus strict/negative type tests, cold/warm compiler experiment sheet, version separation and TS/Bun catalog. |
| `remove-unneeded-compatibility-code` | 3 → 11 | Supported-target proof, callers and artifact consumers, negative evidence limits and targeted removal checks. |
| `reproduce-software-bugs` | 5 → 13 | Exact environment/input, minimal distinguishing reproducer, stable failure oracle and reduction without changing the bug. |
| `test-implementation-behavior` | 20 → 27 | Contract oracles, independent expected results, mutation sensitivity, valid alternatives and appropriate host integration. |
| `update-changelogs` | 11 → 17 | Shipped-change evidence, repository format, release grouping, honest user impact and retained tested validators. |
| `write-agents-md` | 4 → 12 | Instruction scope/inheritance, verified repository commands, concise ownership rules and parent/child conflict avoidance. |
| `write-implementation-plans` | 6 → 14 | Repository-grounded sequence, dependencies, file boundaries, acceptance checks and decisions left with their owner. |
| `write-justfiles` | 7 → 14 | Native Just syntax, recipe parameters/dependencies, shell boundaries, working directories and checker limitations. |

## Observed validation

### Repository and fixture integrity

`python3 scripts/validate_repository.py` and
`python3 scripts/validate_assets.py` both returned exit 0 on
the final tree. They cover the repository's metadata/body
constraints, native descriptors, local Markdown paths and
asset syntax according to their implemented scope. The new
`check_evals.py` checked all 44 skills: 132 task cases, 453
assertions, 132 fixture references and 176 discovery cases.
Its own 11 tests passed. Hash comparisons verified every
imported catalog and all 30 source-layout files. Original
non-skill file bytes, all 44 identities and native
invocation policies were checked for preservation.

### Python tests

Across observed module and split-method runs, **179 test
methods passed and 3 were skipped**, totaling 182. Skips are
one actual Sublime-host test and two tests requiring Just.
No skipped host test is treated as evidence of host
correctness.

The original sequential Python runner timed out. A bounded
per-module attempt collected 20 complete module logs but the
large changelog validator suite exceeded that attempt's
window. A separate changelog run logged 13 methods passing
before its timeout; the final two methods then passed in a
targeted run. Thus every listed method has an observed
outcome, but there was **not one uninterrupted successful
full runner invocation**. Logs and the machine-readable
audit preserve that distinction.

### Native example and harness checks

| Target | Actual environment | Observed result |
| --- | --- | --- |
| C | GCC 14.2.0; C11 | Release/warnings-as-errors and AddressSanitizer + UndefinedBehaviorSanitizer checks passed. |
| C++ | G++ 14.2.0; C++17 | Release/warnings-as-errors and AddressSanitizer + UndefinedBehaviorSanitizer checks passed. |
| Go | Go 1.23.2, Linux amd64 | Independent/ownership tests, race check and native benchmark smoke passed with network disabled. |
| Java | javac 21.0.11 | Kernel compilation and independent behavior checks passed. JMH not executed. |
| Kotlin | Kotlin/JVM 1.9.0, JRE 21.0.11 | Kernel, independent behavior, repeatable Sequence and constrained-consumption checks passed. JMH not executed. |
| Swift | Swift 6.2.1, x86_64 Linux | Optimized kernel and ownership checks passed. Apple XCTest performance integration not executed. |
| JavaScript | Node 22.16.0 | Four `node:test` cases passed; exploratory timing smoke produced eight raw samples. |
| TypeScript | TypeScript 5.8.3, Node 22.16.0 | Strict compilation and runtime checks passed. An isolated `any`-widening mutation failed both negative type oracles as expected. This is not a TypeScript 7 validation. |
| Python | Python 3.13.5 | Three kernel/ownership tests passed; pyperf timing was not run. |

Go timing used `-benchtime=20ms -count=3` as a **harness
smoke check**, not evidence of a production speedup or a
statistical acceptance gate. JavaScript samples are
explicitly same-process exploratory timing. Neither is
presented as a general performance result. The TypeScript
verification used the installed compiler directly as a
documented validation fallback because Bun was unavailable;
the packaged Just recipe still uses `bunx --no-install tsc`
and does not change the actual Node application runtime.

### Checks not completed

`just validate` could not run: `just` was unavailable, as
were Bun, skills-ref, Ruff, Pyright and ShellCheck. The
uploaded root refers to `.markdownlint-cli2.jsonc`, but that
root file is absent; no replacement lint policy was
invented. Container network lookup also prevented
provisioning attempts. The original root
recipes/configuration remain unchanged. Local metadata/asset
checks are not reported as the upstream `skills-ref`,
Markdown, Ruff-format, Pyright, ShellCheck or Just checks.

.NET SDK, Rust/Cargo, Scala tooling and several real
editor/emulator hosts were not available. Therefore .NET
10/C# 14, Rust, Scala, JMH/Google Benchmark/optional
Criterion, pyperf, Apple XCTest performance, and real
editor/emulator integrations were not executed here.
Preserved examples and newly added integration templates
remain subject to those target-native checks. The Go >=1.24
`B.Loop` template was not compiled with Go 1.23.2.

**No fresh-agent skill-versus-baseline evaluations were
run.** The 132 task fixtures and 176 discovery cases are
authored inputs with validated structure, not a measured
improvement in task success, activation accuracy, tokens or
latency. The current cases emphasize bounded review and
authority/semantic boundaries; real implementation tasks in
sanitized target repositories remain necessary to assess
end-to-end agent effectiveness.

## Evidence files

[Machine-readable audit](skills-audit-2026-09-20.json)
contains the complete added/changed/ removed-file inventory,
per-skill counts, ecosystem-index inventory, native-check status, missing
tools and Python test accounting.
[Validation observations](validation-2026-09-20/) contains
fixture-check output, captured test logs and exploratory
timing smoke output. Compiler binaries, temporary mutated
sources, generated caches and internal build-generation
scripts are not packaged. Published skills do not depend on
these internal audit files.
