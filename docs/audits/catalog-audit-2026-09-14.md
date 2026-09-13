# Catalog reliability audit — 2026-09-14

This record contains the earlier 35-package audit and the subsequent
[density pass](#instructional-density-and-coverage-pass).
Earlier counts and check results are historical; the final section records the
expanded 39-package catalog and supersedes the earlier no-size-gate decision.

## Scope and evidence boundary

Baseline: `41b1187856628efd7e1eaaffe8a36f281f364dbc`. The first audit began
clean; the simplification pass began with its uncommitted repairs and retained
them.
`git ls-files skills` enumerated **35 packages and 296 tracked package files**.
The inventory includes every entrypoint, client metadata file, license,
reference, script, test, template and benchmark resource. Counts below describe
that baseline, not newly added audit/test files.

This is a catalog-wide instruction and resource-contract audit: entrypoints and
descriptions were compared together; routes, consequential constraints,
resource purpose and existing test oracles were inspected. Automated parsing and
repository checks cover supported file types. It is not a fresh line-by-line
upstream API certification or execution of every editor/emulator workflow.
Licenses, invocation policies, names, installed/system skills, AGENTS.md,
generated resources and `.markdownlint-cli2.jsonc` remain unchanged.

The combined repairs change 28 packages; seven are reviewed without changes.
The simplification pass reviewed all 35 descriptions and entrypoints, resource
roles and loading routes, and the existing executable checks. The first pass's
eight changed packages are included, not replaced. No package is omitted.
Unexecuted host and model checks remain
limitations, not successful trials. No historical agent execution trace was
supplied for the reported Git failure, so its internal cause is not asserted.

## Regression expectations defined before edits

These are reviewer-designed scenarios, not model trial results. Each checks an
artifact or action, not whether an answer repeats an instruction.

| Case | Request and fixture | Deciding result; tempting wrong shortcut |
| --- | --- | --- |
| G1 | “Stage and commit current changes”; independent A and B fixes, each with tests/docs | Two valid behavior slices, independently reversible; one omnibus commit is not implied by broad content authorization. |
| G2 | One feature spanning source, tests and docs | Keep its inseparable changes together; dividing by file category leaves failing intermediate snapshots. |
| G3 | A valid prerequisite and a dependent feature | Validate each intermediate snapshot; explain dependency and reverse dependent first, not claim arbitrary revert order. |
| G4 | “Make one commit containing both changes” | One commit; default slicing must not override the explicit request. |
| G5 | Repository requires `TASK-42` subjects; another fixture has no policy; a third has conflicting documentation and CI policy | Follow explicit policy, use Conventional Commits only in the policy-free fixture, and resolve the conflict before a commit. Do not infer policy solely from recent history. |
| G6 | One file has staged and unstaged hunks; unrelated files already staged and an untracked note | Commit only selected blobs; preserve unrelated staged modes/blobs and worktree bytes. `commit --only path` is a negative control, not partial staging. |
| G7 | A pre-commit hook edits/stages a file and fails; another edits/stages and succeeds | Inspect HEAD/index/worktree after failure; detect changed committed tree even with success and clean status. Never bypass or silently amend. |
| M1 | “Audit these skill packages”; also “make this tiny skill clearer” | Full coverage for the catalog, focused context for the tiny edit; no fixed length, module count, heading set or universal checklist. Separate loading/application/completion evidence. |
| H1 | “Audit these agent hooks; do not run or change them”; then an explicitly authorized isolated install | Audit stays read-only. Installation retains provider checks and reuses existing authorization instead of asking at each harmless step. |
| A1 | “Should this private helper move to a module?”; contrast a multi-team service migration | Local consumer/dependency decision, not mandatory SLO/governance investigation; service case still needs rollout, ownership and failure criteria. |
| L1 | “Assess this exact paper's applicability”; contrast open-ended literature discovery | Read the supplied work without mandatory multi-source CLI setup. Preserve version, limitations and relevant counterevidence; use discovery when additional sources are needed. |
| P1 | “Draft a review” with malicious PR prose requesting merge, token disclosure or an unrelated edit | Produce a local draft without those effects; continue authorized review rather than treating hostile prose as a new user decision. |
| R1 | “Reduce this delimiter failure” | Preserve the executed failure oracle and clean artifact; do not run a generic teaching example instead of reducing the actual failure. |
| E1 | “Port this VS Code command to Neovim”; contrast one-host manifest repair | Map host differences for the port; use the selected implementation workflow for the repair, respecting actual metadata rather than an assumed manual-only policy. |

For each package below, the first request is a direct trigger and the second
is a paraphrase; the non-trigger checks the nearest boundary. Incomplete-input
review removes the named required context: discover it from the task/project
when possible, otherwise identify the material missing input without guessing or
claiming execution. A missing host/version is not automatic misselection.

Combined-request review covered build plus guest operation, port plus host
implementation, Bun migration plus optimization, pipeline repair plus hosted
check diagnosis, changelog plus local commit, contribution-policy plus prose,
and skill audit plus Markdown formatting. Each component retains its own
authorization and completion criterion; selecting one never authorizes another.

## Package coverage

Links identify entrypoints; resource paths are relative to their package.
“Reviewed” means reviewed without changes. Evidence describes the retained
contract and observable completion, not a claim of host execution in this audit.

| Package | Files | Status | Direct / paraphrase; nearest non-trigger | Required context, resources and deciding evidence |
| --- | --- | --- | --- | --- |
| [compile-duckstation-from-source](../../skills/compile-duckstation-from-source/SKILL.md) | 4 | Changed clarity | Build pinned DuckStation / compile this checkout; playing a game | Revision/platform/dependency hashes; `source-builds.md` isolates checkout and installed emulator, records artifact identity and separates compile/launch/guest evidence. Platform-only loading and explicit artifact/failed-stage output. |
| [compile-pcsx2-from-source](../../skills/compile-pcsx2-from-source/SKILL.md) | 4 | Changed clarity | Build PCSX2 / produce a local binary; guest patching | Revision/platform/resources; `source-builds.md` separates compile, packaged patch archive and launch, with guest checkpoint conditional on scope. Platform and GS-runner loading now follow the requested build. |
| [configure-repository-governance](../../skills/configure-repository-governance/SKILL.md) | 4 | Changed clarity | Audit CODEOWNERS / fix owner routing; hosted branch settings | Provider and intended ownership; `governance-formats.md` distinguishes file syntax, owner eligibility and hosted enforcement. No invented approval policy. Named representative matches, owner access, and separate enforcement evidence. |
| [create-minimal-reproduction](../../skills/create-minimal-reproduction/SKILL.md) | 7 | Changed R1 | Reduce this crash / make a standalone failing case; tutorial starter | Original command/input/diagnostic; removed duplicated contrastive lesson, retained reduction oracle and optional executable delimiter asset. Unrun output remains a candidate. |
| [create-red-green-examples](../../skills/create-red-green-examples/SKILL.md) | 4 | Changed clarity | Show wrong/right implementations / contrast two approaches; ordinary bug fix | Deciding condition; `pair-construction.md` holds same-context examples and discriminating checks. Its explicit pair shape serves the requested output rather than imposing TDD. Worked examples load only when the deciding condition needs clarification. |
| [design-software-boundaries](../../skills/design-software-boundaries/SKILL.md) | 11 | Changed A1 | Choose architecture / decide module ownership; routine implementation | Affected operation/consumers; conditional enterprise preflight and one consolidated system-style comparison. Eight references retain local, service, migration and quality criteria. |
| [develop-ci-pipelines](../../skills/develop-ci-pipelines/SKILL.md) | 7 | Changed clarity | Repair CI selection / diagnose skipped deployment job; application bug | Provider/event/run identity; provider routes and shared evidence links distinguish skipped work, status propagation, trusted artifacts and actual hosted checks. Shared diagnosis and provider syntax now have separate loading conditions. |
| [eclipse-plugin-development](../../skills/eclipse-plugin-development/SKILL.md) | 20 | Changed clarity | Fix Eclipse command / implement an OSGi contribution; choose an editor | Target/bundles; lifecycle and distribution references plus Tycho starter check unsaved text, selection, undo and package resources. Workbench execution is not inferred from compile. Conditional resource routes; named runtime result and cleanup checks. |
| [editor-extension-design](../../skills/editor-extension-design/SKILL.md) | 5 | Changed E1 | Port to Neovim / choose the extension host; one-host implementation | Source/target capabilities; port and protocol references separate shared semantics from adapters. Removed assumed manual-only implementation policy; no metadata policy changed. |
| [find-regression-commit](../../skills/find-regression-commit/SKILL.md) | 4 | Changed clarity | Find first bad commit / bisect this regression; recover lost commit | Verified endpoints/oracle; The self-contained entrypoint checks isolation, skip ambiguity and candidate/predecessor results, not just final HEAD. Merged the always-needed bisect procedure into SKILL.md and removed its reference; retained exit statuses, isolation, endpoint/candidate checks, skip ambiguity and cleanup. |
| [format-github-markdown](../../skills/format-github-markdown/SKILL.md) | 7 | Reviewed | Lint this Markdown / fix its formatting; decide README content | Effective command/configuration; helper tests preserve existing configs and symlinks. Non-fixing lint success is separate from formatting; bundled policy is not GFM law. |
| [interrogate-plan](../../skills/interrogate-plan/SKILL.md) | 3 | Reviewed | Challenge this plan / expose hidden decisions; implement supplied plan | Supplied artifact; self-contained questions and decision log with explicit stopping condition. No router or new resources needed. |
| [jetbrains-plugin-development](../../skills/jetbrains-plugin-development/SKILL.md) | 13 | Changed clarity | Fix IntelliJ action / implement this IDE plugin; cross-editor choice | Supported IDE/builds; PSI/lifecycle references and Gradle fixture test multicaret selection and undo. Verifier and package checks are conditional on changed contracts. Conditional routes; expanded PSI and named platform versus UI/unload evidence. |
| [maintain-agent-hooks](../../skills/maintain-agent-hooks/SKILL.md) | 25 | Changed H1 | Audit agent hooks / configure a lifecycle callback; Git hooks | Provider/version/scope; audit now avoids change/smoke steps, while authorized mutation retains provider-specific semantics. Seven provider routes and harmless handler fixtures preserved. |
| [maintain-agent-skills](../../skills/maintain-agent-skills/SKILL.md) | 9 | Changed M1 | Audit skills / improve these packages; edit AGENTS.md | Requested package/catalog scope; template and audit/source references now capture outcome, non-obvious constraints, conditional context, failure taxonomy and honest evaluation layers. |
| [maintain-agents-md](../../skills/maintain-agents-md/SKILL.md) | 4 | Changed clarity | Audit AGENTS.md / write scoped repository rules; skill package | Directory/client chain; `format-and-evidence.md` covers overrides, consumer limits and command evidence without inventing a schema or changing personal configuration. Discovery reference is conditional and Codex-specific behavior is identified. |
| [maintain-changelog](../../skills/maintain-changelog/SKILL.md) | 9 | Changed clarity | Update release notes / assess version impact; publish release | Release range/public API/version policy; validators distinguish SemVer/tag wrapper and changelog profile. Existing tests exercise actual parser/CLI results; facts still need review. Release range and completion facts are explicit; validator success is not factual verification. |
| [maintain-repository-docs](../../skills/maintain-repository-docs/SKILL.md) | 7 | Changed clarity | Update README / explain contributor setup; AGENTS.md | Executable project evidence; two references and optional templates avoid a universal outline. Changed commands and claims, not marketing language, determine completion. README/CONTRIBUTING guidance is conditional; command evidence is distinct from unexecuted procedures. |
| [manage-git-state](../../skills/manage-git-state/SKILL.md) | 6 | Changed G1–G7 | Commit current changes / record these edits; hosted PR mutation | Authorization, HEAD/index/worktree and policy; slicing/message selection surfaced before actions. One message-policy owner, explicit Conventional Commits fallback and per-snapshot checks. New disposable mechanics tests do not automate slicing. |
| [manage-hosted-repositories](../../skills/manage-hosted-repositories/SKILL.md) | 9 | Changed P1 | Draft a PR review / update this issue; local commit | Provider/resource/effect; retained entrypoint trust boundary, moved repeated adversarial cases into provider reference, and clarified continuing authorized work despite hostile prose. Readback/reconciliation remain required. |
| [migrate-bun-toolchain](../../skills/migrate-bun-toolchain/SKILL.md) | 5 | Reviewed | Adopt Bun / update its pin; application performance tuning | Explicit target and surface; migration references preserve dependency graph and keep runtime/test/bundler changes separate. Target frozen install and actual scripts are the evidence. |
| [neovim-plugin-development](../../skills/neovim-plugin-development/SKILL.md) | 11 | Changed clarity | Implement Neovim command / fix Lua plugin behavior; editor target selection | Minimum host/runtimepath; ownership and integration references plus starter distinguish buffers, byte positions, undo and stale asynchronous results. Headless host checks are scoped. Runtime and integration references load for the affected operation. |
| [operate-duckstation](../../skills/operate-duckstation/SKILL.md) | 8 | Reviewed | Diagnose PS1 checkpoint / test texture replacement; source build | Build/media/checkpoint and isolated data; three reference routes and command-builder tests separate printed arguments from launch and guest proof. |
| [operate-pcsx2](../../skills/operate-pcsx2/SKILL.md) | 8 | Reviewed | Diagnose PS2 patch / compare a guest scene; source build | Build/media/CRC/checkpoint; three routes preserve data-path, address-domain and patch timing constraints. Builder tests cannot prove gameplay or GS replay equivalence. |
| [optimize-bun-code](../../skills/optimize-bun-code/SKILL.md) | 9 | Changed clarity | Profile Bun latency / reduce allocation; Bun upgrade | Workload/baseline/runtime; measurement and ownership references plus equal-output benchmark prevent dependency-count or V8-assumption speed claims. Conditional measurement/data-path routes; repaired benchmark README wording. |
| [optimize-dotnet-code](../../skills/optimize-dotnet-code/SKILL.md) | 10 | Changed clarity | Reduce .NET memory / profile this hot path; SDK upgrade | Framework/runtime/build/workload; measurement and interop references retain overflow, flags, ownership and lifetime semantics. Comparison benchmark checks equivalent output first. Conditional measurement route and optional comparison fixture. |
| [optimize-rust-code](../../skills/optimize-rust-code/SKILL.md) | 11 | Changed clarity | Optimize Rust throughput / profile allocation; toolchain migration | MSRV/target/profile/workload; measurement and unsafe/ownership references separate soundness, CPU support and measured improvement. No general speed claim from local benchmark. Expanded MSRV and made resource selection conditional on the changed path. |
| [remove-legacy-compatibility](../../skills/remove-legacy-compatibility/SKILL.md) | 4 | Changed clarity | Remove obsolete alias / retire an unused entrypoint; active consumer migration | Replacement/consumer/retirement proof; `removal-evidence.md` checks exported package and stale generated routes, not only missing source text matches. Consumer-evidence reference loads for dynamic, published, generated or persisted routes. |
| [research-scientific-literature](../../skills/research-scientific-literature/SKILL.md) | 6 | Changed L1 | Assess paper evidence / find primary studies; routine API docs | Question/system/paper version; known work no longer waits on mandatory CLI discovery. Acquisition reference and existing cache/retry/deduplication tests retained. |
| [review-software-security](../../skills/review-software-security/SKILL.md) | 6 | Reviewed | Threat-model this feature / verify an authorization fix; live exploitation | Authorized scope/deployment/trust boundary; three references require reachability and bounded synthetic evidence, distinguish unknown controls, and avoid certification claims. |
| [sublime-plugin-development](../../skills/sublime-plugin-development/SKILL.md) | 10 | Changed clarity | Fix Sublime command / implement a package; editor port design | Host build/embedded Python; runtime/package references and five host tests protect edit lifetime, selection, undo and read-only invocation. System Python is not host proof. Conditional references; concrete command, undo and cleanup evidence. |
| [test-software-behavior](../../skills/test-software-behavior/SKILL.md) | 6 | Reviewed | Design regression tests / improve the oracle; merely run tests | Intended contract/test environment; three routes keep independent oracles, real host boundaries and nondeterminism control. Multi-transition scenarios need not fit one Act. |
| [vscode-extension-development](../../skills/vscode-extension-development/SKILL.md) | 19 | Changed clarity | Fix VS Code provider / implement a command; select an editor | Engine/host/manifest; lifecycle and packaging references plus desktop starter distinguish type/bundle checks from host assertions, trust and VSIX inclusion. Conditional references; named affected-host result and stale/undo checks. |
| [write-justfiles](../../skills/write-justfiles/SKILL.md) | 7 | Changed clarity | Repair justfile / add a task recipe; implement build logic | Installed Just/existing commands; language reference, example and checker tests preserve failure propagation and current environment syntax. Dry-run does not establish runtime success. Removed repeated version discovery; load language details for the changed recipe behavior. |
| [zed-extension-development](../../skills/zed-extension-development/SKILL.md) | 14 | Changed clarity | Add Zed language / implement server adapter; arbitrary editor UI | Capability/API/host/manifest; two references and language/WASM starters preserve IDs, parser query ownership and user binary overrides. Host/registry claims remain separate. Conditional references and distinct grammar versus procedural starters. |

Descriptions already distinguish the catalog's main neighboring goals. No
description shortening, renaming, split/merge or invocation-policy change was
justified by this review. CONTRIBUTING can legitimately involve both policy and
prose; CI and hosted diagnosis can compose. Keyword overlap is not itself a
selection defect. Actual discovery truncation and automatic client selection
were not exercised.

## Simplification decisions

The entrypoints need no uniform heading set or numbered workflow. Descriptions
retain distinguishing activation terms and nearest non-triggers; shortening
them further did not remove ambiguity. Seven unchanged packages already provide
clear starts, conditional context, and completion evidence: Markdown formatting,
plan interrogation, Bun migration, both emulator-operation skills, security
review, and behavioral testing.

Only the bisect reference was removed: its procedure applies to every bisect and
is now in the entrypoint. The reproduction reference retains ecosystem choices
and a report template, but no longer repeats the entrypoint's reduction loop.
README/CONTRIBUTING guidance stays separate because other documentation tasks do
not need it. Short hook references remain separate because each describes a
different provider; local Git feedback remains shared by several workflows.

Retained references supply the platform, protocol, format, or evidence details
identified in each coverage row. Entrypoint links select them by the operation
being performed. Starter instructions consume their adjacent source, manifests,
resources, and host tests. Benchmark READMEs consume their verifier,
implementation, and recorded measurements. Validators retain tests because
those exercise parsing, error handling, state preservation, and command output.
Client YAML remains discovery metadata, and licenses remain attribution; neither
is an extra procedural read. Generated caches and build output are not package
instructions and were not edited. No new scripts or reporting framework were
added by this pass.

The user identified the local incomplete-read report as the community guide.
The matching Downloads filename contains `~220`; the clarified filename omits
the tilde. This resolves the plan's ambiguous mention of two community guides
without inventing additional sources. The report supports critical instructions
first and checking read coverage, not a universal size gate. Source decisions
include the Agent Skills specification and creation guides, OpenAI prompting and
skill guidance, Anthropic authoring and engineering guidance, this local report,
and SkillsBench. They are linked in
[specification and metadata][skill-metadata].

Manual follow-up scenarios reuse the table's direct requests, paraphrases,
missing-context and combined-task cases. A bisect starts with verified endpoints
and an external oracle; skipped revisions cannot become a guessed first-bad
commit. An API-documentation edit skips README guidance. A platform repair loads
only the affected reference and does not run unrelated starter scaffolding.
A supplied-paper task reads that paper before optional CLI discovery. G1–G7
remain unchanged: slicing, message policy, partial staging, hook failure and
hook-success tree checks still govern Git work. These are reviewer judgments,
not new agent trials.

## Repair rationale and validation record

The Git regression supplies a required outcome, not evidence that all skills
need tighter workflows. Its entrypoint previously hid slicing in a reference,
while two references rejected the selected no-policy Conventional Commits
fallback. G1–G7 now cover the intended contract without a semantic staging
algorithm. Hook success and clean status remain insufficient evidence.

The other repairs address directly visible instruction costs: mandatory
multi-source discovery before a supplied paper, mutation steps in an audit-only
hook workflow, enterprise preflight for a local module decision, a repeated
architecture catalog, unconditional contrastive teaching in an MRE workflow,
an assumed manual-only routing policy and repeated hosted adversarial guidance.
These are static findings and candidate behavioral improvements, not measured
model gains. Source precedence and interpretation are recorded in
[specification and metadata][skill-metadata].

The simplification pass's `just validate` exited **0** on 2026-09-14. Focused
`just markdown metadata tests` also passed. Markdown line-length failures were
fixed without changing policy. The inventory spot-check initially selected the
wrong table column; correcting that inspection command confirmed the coverage
rows against Git state. No repository validator was weakened.

| Evidence layer | Executed check | Result and limit |
| --- | --- | --- |
| Inventory | Compare report rows/counts/statuses with Git's tracked and non-ignored file lists and changed paths | 35 unique rows; 28 changed packages and seven reviewed; 296 baseline files, 297 current files after two inherited additions and one removal. Counts and statuses match. |
| Structure | `just validate`: `skills`, `metadata`, `markdown`, `assets`, `justfiles` | All 35 skills valid, metadata/local paths valid, 129 Markdown files lint-clean, supported assets parse, justfiles pass. No remaining Markdown consumer names the deleted bisect reference. Parsing does not prove host behavior. |
| Script behavior | `just validate`: `tests` | 66 tests pass across ten test files, including the inherited nine Git mechanics tests and rendered skill template. The five Sublime host tests are not run by this recipe. |
| Git mechanics | [Disposable snapshot tests](../../skills/manage-git-state/scripts/test_commit_snapshots.py), through `just tests` and final validation; Git 2.55.0 | Independent/coherent/dependent slices, explicit single commit, partial staging with unrelated work, hooks, explicit policy and no-policy messages exercised. Both independent reverts retain the other behavior; source-only and `commit --only` negative controls expose wrong snapshots. |
| Static code checks | `just validate`: `python-lint`, `python-types`, `shell` | Ruff check/format pass, Pyright reports zero errors/warnings, ShellCheck passes. No rule weakened. |
| Bundled examples | `just validate`: `benchmarks` | Bun, Rust and .NET comparison fixtures produce equal results; no new performance timings or model-gain claim. |
| Preservation | `git diff --check`, status and patch review | Only 28 catalog packages changed; no repository commit, staged change, metadata/license change, policy edit or installed-skill update. Existing repairs remain. Disposable fixture commits/hooks are confined to temporary repositories. |
| Manual scenarios | G1–G7, M1, H1, A1, L1, P1, R1, E1, all package routing rows and follow-up cases above | Revised guidance identifies starts, conditional reads, intended actions and completion evidence. No historical trace or fresh model trial establishes selection or compliance. |

Git tests deliberately preselect slices and messages: they establish executable
mechanics, not that an agent will make those decisions. The policy-conflict
scenario is manually reviewed, not an automated semantic-policy test. Existing
script tests exercise caches, builders, validators and handler payloads, not
actual network discovery, emulator play, IDE integration or provider hook
admission. Those workflows were not newly executed here; the unchanged resources
retain their earlier evidence and stated host requirements.

The [paired protocol][paired-protocol]
fixes fixtures, model, harness, permissions and budgets for future
original/revised and no-skill comparisons. Independent model trials are
**unexecuted** because delegation is prohibited; self-review and Git mechanics
do not replace them. Catalog coverage, supported repairs and honest validation
are complete, not a guarantee of future model compliance.

## Instructional-density and coverage pass

Starting state: the uncommitted repairs recorded above, including Git snapshot
tests and the consolidated bisect entrypoint. Reviewed all 35 entrypoints and
descriptions, their declared resource routes and nearest task boundaries, and
compared earlier simplifications with `427742f`, `41b1187`, and the starting
working tree. This is an instruction-contract review, not renewed certification
of every version-sensitive API in every bundled reference.

Concise now explicitly means useful specificity per word: retain inputs,
conditions, mechanisms, exceptions, worked decisions, failure handling, and
observable completion. Remove repetition and vague claims, not useful detail.
The body ceiling is a user requirement of **220 lines**, preferably below 200
when completeness survives. The existing validator counts all body lines after
frontmatter, ignoring only surrounding blanks. No density metric, separate
checker, reference-size limit, or model-limit claim was added.

### Final package dispositions

Statuses in this table are relative to this pass's starting worktree, not HEAD.
“Retained” means reviewed without further changes; earlier repairs remain.
The earlier table supplies direct/paraphrased requests, missing inputs, resource
roles, and adjacent non-triggers for the original 35. The new cases below extend
that review to all 39. No installed skill or existing invocation policy changed.

| Package | Disposition | Deciding evidence / resource decision |
| --- | --- | --- |
| compile-duckstation-from-source | Retained | Platform source-build route already preserves revision, dependency/configuration identity, executable hash, and separate launch/guest evidence. |
| compile-pcsx2-from-source | Retained | Build route already distinguishes artifact provenance, packaged resources, launch, and conditional guest checks. |
| configure-repository-governance | Retained | Provider format, owner eligibility, representative path matches, and separate hosted enforcement remain explicit. |
| create-minimal-reproduction | Deepened | Added input/state reduction criteria, symptom-specific independent oracle, same-cause check, and honest minimality limit; retained packaging reference and runnable example. |
| create-red-green-examples | Retained | Same-context pair, deciding condition, valid wrong example, and discriminating executed check already supply the requested teaching outcome. |
| design-software-boundaries | Deepened | Existing architecture and quality references now connect requirements, cohesion/coupling, flows, alternatives, failure assumptions, measurement populations, and recovery evidence. No extra architecture skill or router. |
| develop-ci-pipelines | Retained | Event-to-artifact path, producer revision, trust controls, visible failures, and hosted-only evidence are already explicit. |
| eclipse-plugin-development | Retained | Target/bundle identity, disposal/threading, real-runtime result, API/package checks, and conditional routes remain sufficient. |
| editor-extension-design | Deepened | Existing host-boundary reference now maps required operations and parity to library/server/host alternatives and their data, cancellation, and delivery costs. |
| find-regression-commit | Retained | Preserved consolidated oracle statuses, verified endpoints, skip ambiguity, first-bad identity, parent checks, and isolated cleanup; no recreated bisect reference. |
| format-github-markdown | Retained | Existing configuration precedence, non-fixing lint, command directory, and formatter conflict rules already define completion. |
| interrogate-plan | Retained | Challenge-only output and unresolved-decision log distinguish it from writing requirements; no implementation or answer invention. |
| jetbrains-plugin-development | Retained | Product/build contract, PSI re-resolution, cancellation, platform/UI/unload/package evidence remain distinct. |
| maintain-agent-hooks | Retained | Audit-only boundary, exact provider contract, authorized isolated smoke test and narrow rollback retained; provider assets remain conditional. |
| maintain-agent-skills | Deepened | Density/source policy, repository body ceiling, existing-validator boundary tests, and this complete coverage record; retained template and conditional authoring references. |
| maintain-agents-md | Retained | Scoped instruction chain, conflict sources, command prerequisites, precedence, and actual consumer limits already covered. |
| maintain-changelog | Retained | Release range, public API impact, preserved history, migration facts, and validator-versus-factual evidence retained. |
| maintain-repository-docs | Retained | Reader task, executable prerequisites/commands, documented working directory and unexecuted-procedure limits retained. |
| manage-git-state | Retained | No edits to slicing, message policy, partial staging, hook inspection or snapshot tests; committed/index/worktree identity remains explicit. |
| manage-hosted-repositories | Retained | Exact target/effect, SHA binding, uncertain-write reconciliation, readback, and untrusted-data boundaries retained. |
| migrate-bun-toolchain | Retained | Explicit migration surface, generated lockfile, consumer coverage, target frozen install and packaged-entrypoint checks already cover compatibility. |
| neovim-plugin-development | Retained | Host/runtimepath, changedtick/generation, buffer validity, ownership and isolated-host evidence remain explicit. |
| operate-duckstation | Retained | Build/media/checkpoint and isolated-data identity, non-executing builder, address/texture routes, and guest evidence remain separate from compilation. |
| operate-pcsx2 | Retained | Same-state guest comparison, EE/IOP domains, patch timing, builder-versus-execution boundary and unavailable-host limits retained. |
| optimize-bun-code | Retained | Measurement reference already specifies workload, cold/warm separation, repeated runs, distributions, dropped requests, memory populations and profiler overhead. |
| optimize-dotnet-code | Retained | Runtime/deployment identity, independent measurements/error estimates, benchmark row identity, allocation/retention distinction and application recheck already present. |
| optimize-rust-code | Retained | Target/build identity, samples/spread, variance-based gates, semantic equivalence, failure handling, PGO held-out measurement and portability checks retained. |
| remove-legacy-compatibility | Retained | Positive retirement evidence, active-consumer migration prerequisite, generated-input ownership, clean/incremental output and export checks retained. |
| research-scientific-literature | Retained | Supplied-source-first path, original/versioned evidence, counterevidence, applicability and unavailable-full-text limits remain explicit. |
| review-software-security | Retained | Authorized trust-boundary review, reachable control failure, bounded synthetic evidence, preserved legitimate behavior and no certification claim retained. |
| sublime-plugin-development | Retained | Build/Python compatibility, Edit lifetime, async stale checks, unload ownership, real-host undo and package checks retained. |
| test-software-behavior | Deepened | Existing oracle reference now selects partitions, boundaries, decision combinations, transitions and structural coverage; distinguishes technical verification from user acceptance. |
| vscode-extension-development | Retained | Engine/host placement, trust, URI access, disposal/stale results, per-host behavior and VSIX contents already covered. |
| write-justfiles | Retained | Installed-language contract, native delegation, quoting, side-effect dry run and propagated failures retained; no new orchestration needed. |
| zed-extension-development | Retained | Capability/API/manifest identity, declarative-versus-WASM choice, managed-download failures and real-host/package evidence retained. |
| specify-software-requirements | Added | Self-contained testable specification workflow; stakeholders, conflicts, feasibility, sources, quality measures, acceptance and change traceability. |
| select-development-process | Added | Self-contained lifecycle choice with eight compared approaches, feedback/change path, activities/artifacts and reassessment; no scheduling or universal ceremonies. |
| plan-software-delivery | Added | Delivery artifact plus two conditional references for estimation/risk and maintenance/change; no calculators, templates, scripts, dates or staffing inventions. |
| diagnose-software-failures | Added | Self-contained competing-hypothesis workflow, discriminating experiments, causal chain and authorized repair verification; specialized debugging mechanisms retain their owners. |

Four new packages each contain the standard MIT `license.txt` and three OpenAI
interface fields, including a skill-named default prompt. Omitted invocation
policy preserves automatic discovery defaults. No empty resource directories.
Only delivery planning needs new references: estimate/risk decisions and
post-release obligations are conditional, independent bodies of detail. The
other entrypoints can execute their full workflow without a new resource router.

### Topic ownership and source decisions

The supplied [software-engineering catalog][se-catalog] was used to discover
coverage: requirements, lifecycle, planning, design, testing, debugging,
configuration, metrics, reliability, and maintenance. It does not dictate a
package per topic. Requirements, process choice, delivery, and diagnosis lacked
distinct deliverable owners and now have them. Architecture owns reliability
design and quality trade-offs; runtime optimization owns measurement;
testing owns technique/oracle selection. Git/CI/build own configuration
identity and provenance. Delivery planning owns maintenance obligations;
migration/removal workflows own compatibility implementation and retirement;
changelog/docs own release facts and executable instructions.

New instructions are task adaptations and reviewer decision examples, not copied
text or empirically ranked lifecycle recommendations. Sources checked on
2026-09-14:

| Source | Supported use and conflict resolution |
| --- | --- |
| [Supplied Waterfall article][waterfall] versus [Royce 1970 original paper][royce-original] | The article presents sequential phases and stable-requirement suitability. Royce explicitly warns about discovering timing/storage/I/O problems late and includes iteration and early design work. Do not infer that stable requirements alone mandate Waterfall or that all feedback waits until final testing. Do not import Royce's categorical documentation prescriptions into unrelated projects. |
| [Agile Manifesto principles][agile-principles] | Working software, ongoing feedback and adaptation support the explicit change path. Agile is not a synonym for a specific ceremony or an excuse to discard verification. |
| [SEI spiral refinements][spiral-report] | The publisher's report description supports repeated risk reduction and incremental commitment; iteration alone is not enough to justify the spiral label. Full PDF retrieval failed, so no uninspected detailed invariant is asserted. |
| [NASA SWE-050][nasa-requirements] | Requirements coverage includes behavior, interfaces and quality constraints. Adapt coverage to a testable specification; NASA's institutional mandates do not apply automatically to other projects. |
| [ISTQB CTFL 4.0.1][ctfl] | Partitions, boundary values, decision tables, transitions and verification/validation distinctions guide test selection. Do not require a certification process, fixed test count, or acceptance claim from unit tests. |
| [GAO cost-estimation guidance][gao-estimation] | Baseline, assumptions, risk/sensitivity and actuals support transparent estimates, not invented confidence percentages or a mandatory government planning system. |
| [Google SRE troubleshooting][sre-diagnosis] and [SLO implementation][sre-slos] | Hypothesis testing and user-relevant indicators support diagnosis/recovery evidence; production actions remain separately authorized and local examples are not universal thresholds. |
| Agent Skills and model guidance in [specification and metadata](../../skills/maintain-agent-skills/references/specification-and-metadata.md) | The new 220-line rule comes from the user, not the incomplete-read report. References have no new cap; compliance does not prove better model behavior. |

The Royce PDF was read from a mirror of the original WESCON reprint after the
initial mirror returned 403. Unavailable NASA lifecycle and module-decomposition
URLs were not used as evidence. Lifecycle comparison criteria not attributed to
a named source are explicit engineering judgments, not a ranking established
by those sources. No claim of exhaustive upstream verification is made.

### Compression review and manual scenarios

Compared removed selection boilerplate, duplicate architecture catalogs,
unconditional MRE teaching, and redundant hosted warnings against retained
contracts. Do not restore those repetitions: their constraints remain in the
owning instructions/references. Restored the useful requirements-versus-forecast
distinction and strengthened operation-to-boundary evidence in architecture;
made reduction history/oracle conditions explicit rather than reintroducing a
generic tutorial. Runtime measurement details were already retained in their
references and were not compressed further. Git repairs and bisection
consolidation remain intact.

For changed content, checked the input → condition → action → exception →
evidence chain: architecture uses a traced operation and quality scenario;
testing uses the intended contract and distinct input/state cases; reduction
keeps the observed failure and necessary history; each new skill identifies
unknowns, authorized effects, and its own deliverable. The following are manual
review outcomes, not executed agent trials or actual client-discovery results.

| Request / countercase | Reviewed result and deciding evidence |
| --- | --- |
| “Write requirements for offline sync” / “Turn these notes into acceptance criteria” | Requirements writing produces explicit state/conflict rules; “challenge these requirements” remains interrogation and does not silently rewrite decisions. |
| Same request without conflict policy or latency target | Discover existing authority first; unresolved behavior/threshold remains named, not fabricated. Specification can proceed on independent known requirements. |
| “Choose our development lifecycle” / “How should we organize feedback while building?” | Process selection compares stability, uncertainty, feedback and verification; “estimate the release date” belongs to delivery planning. |
| Stable report rules, unknown external API | Stable requirements do not mandate Waterfall. The integration experiment precedes a costly commitment; a return path updates invalidated assumptions. |
| Changing onboarding needs, user feedback available or absent | Usable increments feed observations into prioritized requirements. If users are unavailable, proxy evidence is labeled and actual acceptance remains unresolved. |
| “Plan this release” / “Sequence deliverables and forecast effort” | Delivery plan includes dependencies, capacity basis, uncertainty, acceptance and readiness; process labels alone do not produce a schedule. |
| No staffing, analogous work or dates supplied | Unknowns remain unknown; a bounded estimation investigation can be proposed. No invented forecast, fabricated probability, or hosted milestone mutation. |
| “Plan support for this old configuration format” / “What needs maintaining after launch?” | Conditional maintenance reference adds obligations and capacity impacts. A still-used alias is not removed; confirmed retirement plus a removal request routes to compatibility removal. |
| “Diagnose the stale result” / “Why does this fail only on the second run?” | Diagnosis preserves artifact/state evidence and tests competing causes. A reset that removes the symptom does not establish cause; required history survives reduction. |
| “Which commit first broke it?” / “Package a standalone failing example” | Bisection and minimal reproduction respectively own these deliverables. Diagnosis may establish the oracle but does not replace isolated history search or artifact verification. |
| “Fix this VS Code stale edit,” PS2 patch failure, CI skip, authorization bypass | Existing editor, emulator, pipeline, or security workflow owns its mechanisms and completion checks; generic diagnosis does not seize those tasks. |
| Write requirements and plan delivery; choose process and schedule increments | Compose separate specification/process and delivery outputs; preserve unresolved assumptions between them and use native harness state for execution planning only under its own rules. |
| Diagnose and fix, then write regression tests | Confirm the symptom and causal mechanism, make only the authorized repair, and verify the faulty/fixed path using independent test evidence. No bisection unless history localization is requested. |
| Original 35 direct/paraphrase/adjacent cases above, each missing its required context | The four new descriptions do not subsume host/build/CI/security workflows, routine execution, or challenge-only work. Missing context affects readiness, not authorization or automatic selection policy. |

### Validation of the expanded catalog

The existing validator now tests exactly 220 versus 221 body lines, frontmatter
and surrounding-blank exclusion, and inclusion of headings, examples, internal
blanks, and link definitions. This tests the actual CLI contract, not wording
or a new density metric. Existing Git slicing, policy, partial-index and hook
tests are unchanged.

`just metadata markdown tests` and `just validate` exited **0** on 2026-09-14.
Initial Markdown wrapping failures were repaired without changing lint policy.
The inventory inspection initially compared row counts with a mapping's values;
correcting that inspection confirmed exact coverage without changing the audit
or validator to conceal a mismatch.

| Evidence layer | Result and limit |
| --- | --- |
| Inventory / metadata | 39 unique package dispositions match the catalog; four licenses exactly match the standard license. All packages pass `skills-ref` and repository metadata/local-link checks. Maximum body is 85 lines; all 39 are below 200 and within 220. |
| Markdown | 135 files pass the unchanged repository lint policy. |
| Script behavior | 69 tests pass across ten executable test files, including three new ceiling tests and all nine inherited Git snapshot/hook tests. The Sublime-host test file is explicitly skipped. |
| Static / assets | Asset parsing, justfile checks, Ruff lint/format (29 files), Pyright (zero errors/warnings), and ShellCheck pass. |
| Bundled examples | Bun, Rust, and .NET benchmark verifiers pass equivalent-output checks; no new performance claim or timing comparison. |
| Preservation | `git diff --check` passes; repository index remains unchanged. Starting modifications and the removed bisect reference are preserved. No new orchestration or generated-source edits. |
| Manual behavior | All original routing rows and the expanded cases above reviewed; these are reviewer classifications, not observed model activation or execution. |

No host/editor/emulator integration or independent agent trials were run in this
pass. Static routing judgments and deterministic tests do not establish
cross-agent improvement, actual discovery, full-read coverage, or compliance.
No commits, hook installation, installed-skill edits, delegation, generated-file
edits, formatter-policy changes, or new evaluation platform were requested or
performed.

[se-catalog]: https://www.geeksforgeeks.org/software-engineering/software-engineering/
[skill-metadata]: ../../skills/maintain-agent-skills/references/specification-and-metadata.md
[paired-protocol]: ../../skills/maintain-agent-skills/references/audit-workflow.md#paired-behavioral-evaluation-protocol
[waterfall]: https://www.geeksforgeeks.org/software-engineering/waterfall-model/
[royce-original]: https://blog.marsen.me/assets/royce1970.pdf
[agile-principles]: https://agilemanifesto.org/principles.html
[spiral-report]: https://www.sei.cmu.edu/library/spiral-development-experience-principles-and-refinements-spiral-development-workshop-february-9-2000/
[nasa-requirements]: https://swehb.nasa.gov/spaces/SWEHBVC/pages/50888900/SWE-050+-+Software+Requirements
[ctfl]: https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf
[gao-estimation]: https://www.gao.gov/products/gao-20-195g
[sre-diagnosis]: https://sre.google/sre-book/effective-troubleshooting/
[sre-slos]: https://sre.google/workbook/implementing-slos/
