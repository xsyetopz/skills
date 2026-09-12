# Supplemental source intake

## Readability and agent failure notes

Reviewed on 2026-09-12. These notes are leads, not normative standards.

- `code-readability-for-humans-and-ai-agents.md` SHA-256:
  `88ee0612b797609e1fbb4ce443e03c2c173048313d025de3522d63ad1d8ea1d1`
- `agent_engineering_problems_and_solutions.md` SHA-256:
  `1f78641a26493515d43d2c1341743255f3ffe5f8ed594d8b986b2a4a4328593f`

The readability document was read in full. Its useful locality, terminology,
semantic-type and visible-error-flow recommendations fit the existing
`design-software-boundaries` language-layout reference. Added a compact local
reasoning section there; no new readability micro-skill or mandatory framework.
The existing reference already rejects LOC-driven fragmentation and speculative
abstractions.

Rejected unsupported CEFR-to-programmer-level mappings and universal numerical
limits on functions, variables, parameters and complexity. Rejected the apparent
review typo asking whether a diff is narrower than necessary. Existing project
lint limits remain authoritative; this intake does not weaken them.

The agent-failure matrix was reviewed selectively: all category/problem names,
with detailed architecture rows. Most entries concern harness authority, tool
protocols, stopping, memory and coordination; duplicating those as a generic
engineering skill would add prompt noise and potentially conflict with active
instructions. Architecture topics already have owners in the boundary, testing,
security, migration and repository-instruction skills. No new catch-all agent
behavior skill was created. This is selective review, not a claim that every
matrix row was independently researched.

The imported design/readability recommendations were checked against Google's
[code-review guidance][review], particularly complexity, names, comments and
context. That source supports these review judgments, not empirical numerical
thresholds or a universal architecture. The change introduces no executable
algorithm; prior architecture routing evaluations remain relevant, while local
Markdown, reference and skill-structure checks cover this reference-only edit.

Both consumed note files were removed after recording their disposition. Other
archives and ecosystem catalogs remain pending selective intake; their presence
is not evidence of incorporation.

[review]:
  https://google.github.io/eng-practices/review/reviewer/looking-for.html

## Language-layout archive

`language-layout-templates.zip` SHA-256:
`909fa8d436f2ad790d9b291ff786fd9164a6c5ddd6fe366c8cb78047c0aa1d75`

Read every source template, Mermaid graph and guide in the archive. Preserved
language-native visibility and locality guidance through the existing layout
reference rather than copying empty classes, dummy imports, placeholder module
paths or a mandatory two-file-per-language scheme. A source-file diagram is not
an architecture or an executable package.

Added the concrete .NET distinction to the existing reference: F# namespaces do
not directly contain value bindings; C# assembly-internal and file-local types
have different visibility boundaries. These were checked against Microsoft's [F#
namespace reference][fsharp] and [C# file modifier reference][csharp].

The F# template was compiled in an isolated .NET 10.0.400 class-library project,
with only its nonexistent illustrative import removed. It failed with FS0201 at
the namespace-level constant. Putting the value in a module built successfully.
Logs are `/tmp/layout-intake-fsharp/build.log` and `corrected.log`. The other
placeholder templates were inspected, not claimed to compile. No unvalidated
skeletons were added to the skill suite. The consumed archive was removed.

## HSP language pack

`hsp-skill-pack-v2.zip` SHA-256:
`1445998b415740f30f6001aff39f67aa18c9a9de5f1a1b4c83640d3e7390d021`

Reviewed the package inventory, entrypoint, upstream source map, source list,
README and project-doctor implementation. The source is a broad HSP language
teaching/porting pack, not a demonstrated missing cross-project engineering
capability in this rebuild. No HSP micro-skill, installer, generated index or
agent-profile layer was imported merely because the archive exists.

The doctor explicitly uses heuristics rather than a parser. Actual execution
reported a missing jump label for `mes "goto *not_a_jump"`, which is quoted
text, not a jump statement. This is evidence that the helper is unsuitable as a
correctness gate, not a claim that its advertised heuristic scan is a compiler.
No HSP compiler/runtime validation or comprehensive language-reference review is
claimed. The pack was declined and removed after this selective disposition;
none of its language claims were imported into maintained guidance.

[fsharp]:
  https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/namespaces
[csharp]:
  https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/file

## .NET performance archives

SHA-256 identities:

- `net8-csharp12-performance-skill.zip`:
  `c2edafe0f529f598168545e691e78c2a26743c7fb1ef151dac7ec87741877cb4`
- `net9-csharp13-performance-skill.zip`:
  `2db586c1cd902e356b8591e8f839f5ec43ee95b15d006b3aa897afb9051b45f3`
- `net10-csharp14-performance-skill.zip`:
  `96cb57c113935f21b9286626c723614f631937fe3cd5b49822be34489a5052f0`

Inventoried all three packages and compared every non-cache text file against
the .NET 10 version. Differences are mostly version labels, language-feature
notes and the forced language setting. Detailed review covered the entrypoint,
optimization and measurement references, source index, benchmark template,
performance props, comparison script, project scanner and justification scanner.
This is selective intake, not verification of every named native binding.

Added one explicit-only `optimize-dotnet-code` category with two references,
rather than three version-specific skills. It preserves the requested runtime
and compiler contract, uses evaluated MSBuild settings, and selects measurement
and memory/interop details conditionally. Current Microsoft and BenchmarkDotNet
sources support imported API and tooling guidance; links are in the references.

Rejected blanket unsafe enablement, unchecked arithmetic, server GC selection,
forced language versions, mandatory comment tokens, keyword-driven hot-path
rewrites, and the custom skill configuration. XML scanning does not evaluate
MSBuild conditions/imports. Comments near unsafe code do not prove safety. The
archive's identical-shape sum microbenchmark is not a production optimization;
no generated caches, mandatory template or native-wrapper inventory was copied.

Actual execution disproved the unconditional `HasFlag` to nonzero-AND rewrite:
composite and zero masks change behavior. The source result comparator also
returned success when the candidate mean was `NA`, and compared .NET 8 and .NET
10 rows as if they were the same runtime. These helpers were not imported. The
new reference preserves all-bits semantics and requires complete, comparable
results.

A real .NET workload, correctness checks, runtime counters, stack sampling and
BenchmarkDotNet run support the replacement guidance. Tool execution also found
that current portable tracing uses `dotnet-sampled-thread-time`, not the
Linux-only `cpu-sampling` profile. See the bounded evidence and limitations in
[.NET evaluation](dotnet-performance-evaluation.md). All three consumed source
archives were removed; the independent ecosystem catalogs remain pending.

## Ecosystem catalogs

Parsed every JSONL record and inventoried package identities and domains. There
were no duplicate identities within each catalog. Detailed review was selective:
metadata policies and representative serialization, database, HTTP,
compiler-tool and standard-library replacement entries. Counts exclude `_meta`
records:

- .NET: 464 entries; SHA-256
  `5bbcfb5e0347f49d9d12dfd20c0b68227af55376af0c6feb043590ab0f61c033`.
- Go: 343 entries; SHA-256
  `7b81ee556cfdaffe344b0dcf990ae4f75d9101197f436c56dc9ad256fec7584d`.
- Rust: 365 entries; SHA-256
  `4e32c2187e26945d2457445514d8b011c268681107a528b0cc8c4ab34051a0db`.
- TypeScript/Bun: 405 entries; SHA-256
  `38de9b7de641318d6ac60d85403ba1df715fc353f8cc80a8414746b8f0d77a51`.

The useful result is a dependency-fit section in the existing architecture
reference, not 1,577 permanent package recommendations, a new dependency-ranking
schema, or four additional language skills. Qualitative weight, maintenance,
AOT, native-code and compatibility labels remain leads rather than certified
properties. No blanket ADD/REMOVE/REPLACE action was imported. Existing package,
compiler and lint policies remain authoritative.

Primary checks used the Cargo feature documentation, Go database/sql and CGO
contracts, modernc SQLite documentation, Microsoft JSON source-generation
guidance, and the actual openapi-typescript package/source. Their links are
adjacent to the imported guidance. In particular:

- `database/sql` is an interface requiring a driver, not a replacement for
  `modernc.org/sqlite`. A real Go 1.27.1 `CGO_ENABLED=0` stdlib-only probe
  failed to open `sqlite` with the expected unknown-driver error. This does not
  claim a particular external driver's full cross-platform compatibility.
- Cargo feature unification means a direct default-features setting cannot
  certify the whole dependency graph. Runtime and native requirements must be
  checked for selected features and targets.
- System.Text.Json source generation requires the actual generated metadata
  path, not merely a package-level AOT label. No new AOT publication is claimed.
- The TypeScript catalog incorrectly calls openapi-typescript
  compiler-independent. The published 7.13.0 package declares a TypeScript 5
  peer; its shipped implementation imports `typescript` and calls the AST
  factory. Source and package metadata disprove the blanket architectural claim
  without needing to claim that every TypeScript 7 arrangement fails.

An isolated Node run of openapi-typescript 7.13.0 with TypeScript 5.9.3
generated response declarations from OpenAPI 3.0.3. Strict type checking
accepted the valid response and rejected an invalid enum value. This verifies
the selected compiler-API integration and generated consumer contract, not
Bun-wide runtime compatibility, every schema feature, or direct TypeScript 7
support. Evidence is in `/tmp/ecosystem-intake-evidence/`. No project compiler
or lint rules changed.

All four catalogs were removed after selective consumption. Their old baseline
versions and unsupported rankings were not converted into evergreen guidance.

## Remaining Rust research disposition

`rust-performance-research.zip` SHA-256:
`54494ae4c51ff1d01e888187ffa5d6231ac235cf84bb52b095ca5734fbe916a3`.

The earlier [Rust evaluation](rust-performance-evaluation.md) records imported
material and real validation. Follow-up intake inspected the full archive
inventory and the scope/evidence, security/performance, CPU-dispatch and unsafe
FFI-buffer chapters. Their useful ownership, adversarial-input, measurement and
portability boundaries are already represented in the two Rust references. No
additional skill or duplicate research/agent-template tree is needed.

The illustrative FFI buffer snippet has undefined external function/error types
and is not a standalone executable asset. Its returned-length check does not
retroactively prevent a foreign out-of-bounds write; the foreign function's
write-capacity and initialization contract must already hold. No claim of FFI
soundness or whole-archive example compilation is made. The remaining archive
was removed after this disposition. Source intake is now complete; that does not
establish completion of the separate whole-suite goal audit.
