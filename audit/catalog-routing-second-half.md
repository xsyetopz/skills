# Routing evaluation: second half of catalog

## Correction note

The initial version incorrectly treated missing execution inputs as preventing
initial skill discovery. The incomplete-relevant rows now select the
identifiable skill and record the inputs still needed to execute safely. The
four editor-port prompts now initially select `editor-extension-design`; their
implementation skills become additional routes only when implementation, rather
than a port plan, is requested. This corrects the evaluation method; it is not a
claim that the catalog metadata changed.

## Defect assessment

No concrete metadata-routing defects found in these 20 packages.

The evaluated descriptions provide meaningful boundaries for neighboring routes:
hosted issues versus pull requests/settings/releases; local Git integration
versus recovery/bisection/commits; documentation/governance/ changelog
separation; Node-to-Bun migration versus Bun performance; and emulator platform
plus patch/texture/run/debug/build separation. The four editor implementation
routes leave editor selection and cross-editor port planning to
`editor-extension-design`. The relevant explicit-only routes
(`format-github-markdown`, `interrogate-plan`) are not selected implicitly.

The reviewer treated the two no-owner cases as bounded non-goals rather than
catalog fragmentation. Coordinator review leaves that conclusion provisional:
metadata alone cannot prove that an excluded workflow needs no specialist
guidance, and the original Bun migration skill also covered Bun-only upgrades.
`migrate-node-to-bun` explicitly excludes Bun-only version upgrades, which are
ordinary dependency/runtime maintenance rather than a distinct migration
capability. `publish-hosted-releases` explicitly excludes local tagging; the
catalog deliberately separates hosted publication from local Git
commit/integration/recovery work, and ordinary local tagging does not require a
specialized workflow. Neither case splits an advertised capability across
competing routes or warrants a new micro-skill.

Scope: the final 20 sorted `skills/*/SKILL.md` entries. Decisions use only
frontmatter and `agents/openai.yaml`, with all 40 catalog metadata entries as
candidate routes. This is a metadata judgment exercise, not client-loader
telemetry.

## maintain-repository-docs

- **Direct positive**
  - **Prompt:** “Write a CONTRIBUTING.md from this repository's actual commands
    and layout.”
  - **Route:** `maintain-repository-docs`
  - **Rationale:** Explicit repository documentation grounded in project
    evidence.
- **Paraphrased positive**
  - **Prompt:** “Audit whether the README's install steps still match how this
    project runs.”
  - **Route:** `maintain-repository-docs`
  - **Rationale:** README accuracy is the stated scope.
- **Incomplete relevant**
  - **Prompt:** “Update the docs.”
  - **Route:** `maintain-repository-docs` — needs the document, intended change,
    and available project evidence
  - **Rationale:** The repository-documentation domain is identifiable; those
    inputs affect execution, not discovery.
- **Nearby other-skill**
  - **Prompt:** “Create issue and pull-request templates for contributors.”
  - **Route:** `configure-repository-governance`
  - **Rationale:** Hosted templates are explicitly excluded here.
- **Unrelated negative**
  - **Prompt:** “Fix the failing OAuth callback.”
  - **Route:** No selection
  - **Rationale:** Runtime implementation is explicitly excluded.
- **Ambiguous**
  - **Prompt:** “Document the next release.”
  - **Route:** Clarification
  - **Rationale:** Could mean release notes/changelog (`maintain-changelog`) or
    general documentation.
- **Composition**
  - **Prompt:** “Update README setup instructions and add a changelog entry for
    the new command.”
  - **Route:** `maintain-repository-docs` + `maintain-changelog`
  - **Rationale:** Separate README and changelog responsibilities.

## manage-hosted-issues

- **Direct positive**
  - **Prompt:** “Create a GitHub issue for the crash and label it bug and
    urgent.”
  - **Route:** `manage-hosted-issues`
  - **Rationale:** Hosted issue mutation and triage.
- **Paraphrased positive**
  - **Prompt:** “Close the GitLab ticket that was fixed in 3.2.”
  - **Route:** `manage-hosted-issues`
  - **Rationale:** GitLab issue lifecycle work.
- **Incomplete relevant**
  - **Prompt:** “Triage this report.”
  - **Route:** `manage-hosted-issues` — needs provider/project, issue identity,
    and requested triage action
  - **Rationale:** It reads as issue triage; provider and target details are
    execution inputs.
- **Nearby other-skill**
  - **Prompt:** “Change the repository's required-reviewer rule on GitHub.”
  - **Route:** `configure-hosted-repositories`
  - **Rationale:** Repository setting, not an issue.
- **Unrelated negative**
  - **Prompt:** “Explain why the build fails locally.”
  - **Route:** No selection
  - **Rationale:** No hosted-issue operation requested.
- **Ambiguous**
  - **Prompt:** “Link the bug to the change request.”
  - **Route:** Clarification
  - **Rationale:** “Change request” may be a GitHub/GitLab PR/MR and the
    requested action is unclear.
- **Composition**
  - **Prompt:** “Open a GitHub issue for the release failure, then comment on PR
    42 with its URL.”
  - **Route:** `manage-hosted-issues` + `manage-pull-requests`
  - **Rationale:** Requires both an issue mutation and a PR comment.

## manage-pull-requests

- **Direct positive**
  - **Prompt:** “Merge GitHub PR #118 after checking its required checks.”
  - **Route:** `manage-pull-requests`
  - **Rationale:** Hosted PR management.
- **Paraphrased positive**
  - **Prompt:** “Review this GitLab merge request and leave the requested-change
    feedback.”
  - **Route:** `manage-pull-requests`
  - **Rationale:** Hosted MR review is in scope.
- **Incomplete relevant**
  - **Prompt:** “Handle PR 12.”
  - **Route:** `manage-pull-requests` — needs provider and intended action
    (review, update, or merge)
  - **Rationale:** The PR domain is explicit; action and provider are execution
    inputs.
- **Nearby other-skill**
  - **Prompt:** “Rebase my local feature branch onto main and resolve
    conflicts.”
  - **Route:** `integrate-git-changes`
  - **Rationale:** Local history integration is explicitly excluded.
- **Unrelated negative**
  - **Prompt:** “Implement the password-reset endpoint.”
  - **Route:** No selection
  - **Rationale:** No hosted PR operation.
- **Ambiguous**
  - **Prompt:** “Merge the change once it is green.”
  - **Route:** Clarification
  - **Rationale:** It may mean a local merge or a hosted PR/MR merge.
- **Composition**
  - **Prompt:** “Review PR #91 for auth flaws and post the security findings on
    it.”
  - **Route:** `review-software-security` + `manage-pull-requests`
  - **Rationale:** Security review and hosted PR feedback are independent steps.

## migrate-node-to-bun

- **Direct positive**
  - **Prompt:** “Migrate this npm TypeScript service from Node and Jest to Bun.”
  - **Route:** `migrate-node-to-bun`
  - **Rationale:** Direct Node/tooling migration to Bun.
- **Paraphrased positive**
  - **Prompt:** “Replace the Yarn/Node test and build workflow with Bun while
    keeping production behavior.”
  - **Route:** `migrate-node-to-bun`
  - **Rationale:** Same migration outcome without using the skill name.
- **Incomplete relevant**
  - **Prompt:** “Move this JavaScript project to Bun.”
  - **Route:** `migrate-node-to-bun` — needs current runtime/tooling and
    compatibility constraints
  - **Rationale:** The migration target is explicit; project details determine
    the migration plan.
- **Nearby other-skill**
  - **Prompt:** “Upgrade this Bun app from 1.1 to the current Bun release.”
  - **Route:** No selection
  - **Rationale:** Bun-only version upgrades are explicitly excluded; no
    matching catalog skill is stated.
- **Unrelated negative**
  - **Prompt:** “Reduce the size of a Rust binary.”
  - **Route:** `optimize-rust-code`
  - **Rationale:** Rust performance work, not a Node-to-Bun migration.
- **Ambiguous**
  - **Prompt:** “Make our tests use Bun.”
  - **Route:** Clarification
  - **Rationale:** Could be a Node-to-Bun migration or an existing Bun test
    configuration change.
- **Composition**
  - **Prompt:** “Migrate this npm service to Bun, then profile the new Bun
    request path for regressions.”
  - **Route:** `migrate-node-to-bun` + `optimize-bun-code`
  - **Rationale:** Migration and evidence-based Bun performance work.

## neovim-plugin-development

- **Direct positive**
  - **Prompt:** “Fix the Neovim Lua plugin's autocmd cleanup when a buffer is
    deleted.”
  - **Route:** `neovim-plugin-development`
  - **Rationale:** Buffer/event lifecycle is explicit scope.
- **Paraphrased positive**
  - **Prompt:** “Review this nvim runtimepath package for leaked timers and bad
    buffer ownership.”
  - **Route:** `neovim-plugin-development`
  - **Rationale:** Neovim plugin resource ownership.
- **Incomplete relevant**
  - **Prompt:** “Repair my Neovim plugin.”
  - **Route:** `neovim-plugin-development` — needs the failing behavior,
    reproduction, and plugin context
  - **Rationale:** Neovim plugin development is identifiable before repair
    details are known.
- **Nearby other-skill**
  - **Prompt:** “Choose whether this formatter extension should target Neovim,
    VS Code, or Zed.”
  - **Route:** `editor-extension-design`
  - **Rationale:** Editor selection precedes an already-selected implementation.
- **Unrelated negative**
  - **Prompt:** “Write a JetBrains PSI inspection.”
  - **Route:** `jetbrains-plugin-development`
  - **Rationale:** Different editor platform.
- **Ambiguous**
  - **Prompt:** “Port my editor extension to Neovim.”
  - **Route:** `editor-extension-design` — needs whether the result is a port
    plan; add `neovim-plugin-development` if implementation is requested
  - **Rationale:** Port planning is the initial route; concrete implementation
    is a separately scoped follow-on.
- **Composition**
  - **Prompt:** “Plan a VS Code-to-Neovim port, then implement the Neovim buffer
    lifecycle.”
  - **Route:** `editor-extension-design` + `neovim-plugin-development`
  - **Rationale:** Plan and platform-specific implementation are distinct.

## optimize-bun-code

- **Direct positive**
  - **Prompt:** “Profile this Bun HTTP handler and eliminate the allocation
    causing the p99 regression.”
  - **Route:** `optimize-bun-code`
  - **Rationale:** Bun performance with allocation evidence.
- **Paraphrased positive**
  - **Prompt:** “Investigate why this Bun service uses more memory after the
    native addon change.”
  - **Route:** `optimize-bun-code`
  - **Rationale:** Bun memory/native-API performance diagnosis.
- **Incomplete relevant**
  - **Prompt:** “Make the Bun app faster.”
  - **Route:** `optimize-bun-code` — needs workload, baseline metric, and
    observed bottleneck
  - **Rationale:** Bun performance is identifiable; measurement inputs are
    needed to execute responsibly.
- **Nearby other-skill**
  - **Prompt:** “Convert this Node service's runtime and tests to Bun.”
  - **Route:** `migrate-node-to-bun`
  - **Rationale:** Migration rather than Bun performance tuning.
- **Unrelated negative**
  - **Prompt:** “Optimize SQL indexes for the analytics database.”
  - **Route:** No selection
  - **Rationale:** No matching catalog performance specialization.
- **Ambiguous**
  - **Prompt:** “The JavaScript API is slow in production.”
  - **Route:** Clarification
  - **Rationale:** Could be Bun, Node, browser, database, or network work;
    metadata excludes non-Bun tuning.
- **Composition**
  - **Prompt:** “Move the Node service to Bun and measure whether its request
    allocations improved.”
  - **Route:** `migrate-node-to-bun` + `optimize-bun-code`
  - **Rationale:** Migration plus post-migration performance validation.

## optimize-rust-code

- **Direct positive**
  - **Prompt:** “Profile this Rust parser and reduce allocations without
    breaking its CPU portability.”
  - **Route:** `optimize-rust-code`
  - **Rationale:** Rust allocation and portability performance work.
- **Paraphrased positive**
  - **Prompt:** “Find why the Rust worker's throughput collapsed after the
    ownership refactor.”
  - **Route:** `optimize-rust-code`
  - **Rationale:** Ownership/concurrency evidence is named scope.
- **Incomplete relevant**
  - **Prompt:** “Speed up the Rust code.”
  - **Route:** `optimize-rust-code` — needs workload, baseline metric, and
    relevant constraints
  - **Rationale:** Rust performance is identifiable; the omitted details affect
    investigation.
- **Nearby other-skill**
  - **Prompt:** “Audit this Rust crate for a deserialization vulnerability.”
  - **Route:** `review-software-security`
  - **Rationale:** Defensive security review rather than performance.
- **Unrelated negative**
  - **Prompt:** “Update the changelog's SemVer prerelease label.”
  - **Route:** `maintain-changelog`
  - **Rationale:** Changelog/version task.
- **Ambiguous**
  - **Prompt:** “Should we use unsafe in this Rust module?”
  - **Route:** Clarification
  - **Rationale:** It may be a performance tradeoff, but may instead be a
    safety/design question.
- **Composition**
  - **Prompt:** “Benchmark the Rust extension core, then adapt its Zed WASM
    integration.”
  - **Route:** `optimize-rust-code` + `zed-extension-development`
  - **Rationale:** Performance analysis and editor-extension integration.

## publish-hosted-releases

- **Direct positive**
  - **Prompt:** “Publish the GitHub release for v2.4.0 and attach the signed
    binaries.”
  - **Route:** `publish-hosted-releases`
  - **Rationale:** GitHub release and assets.
- **Paraphrased positive**
  - **Prompt:** “Verify that the GitLab release page contains every artifact
    from this build.”
  - **Route:** `publish-hosted-releases`
  - **Rationale:** Hosted release verification.
- **Incomplete relevant**
  - **Prompt:** “Release version 2.4.”
  - **Route:** `publish-hosted-releases` — needs confirmation of hosted
    publication, provider, selected version, and assets
  - **Rationale:** “Release” initially routes to hosted release work; local
    tagging/version selection remain excluded and must be disambiguated before
    execution.
- **Nearby other-skill**
  - **Prompt:** “Choose the next SemVer version and write its release notes.”
  - **Route:** `maintain-changelog`
  - **Rationale:** Version selection and release-note writing are explicitly
    excluded.
- **Unrelated negative**
  - **Prompt:** “Create a local annotated Git tag.”
  - **Route:** No selection
  - **Rationale:** Local tagging is explicitly excluded and no catalog skill
    owns it.
- **Ambiguous**
  - **Prompt:** “Ship the release.”
  - **Route:** Clarification
  - **Rationale:** Could mean hosted publication, changelog work, packaging, or
    local tagging.
- **Composition**
  - **Prompt:** “Write the v2.4.0 release notes, then publish the GitHub release
    with artifacts.”
  - **Route:** `maintain-changelog` + `publish-hosted-releases`
  - **Rationale:** Content authoring and hosted publication divide cleanly.

## recover-git-state

- **Direct positive**
  - **Prompt:** “Recover the local commit I lost after resetting this branch
    yesterday.”
  - **Route:** `recover-git-state`
  - **Rationale:** Lost local commit recovery.
- **Paraphrased positive**
  - **Prompt:** “Discard only the identified generated-file changes while
    keeping my unrelated edits.”
  - **Route:** `recover-git-state`
  - **Rationale:** Deliberate restoration/discard with preservation constraint.
- **Incomplete relevant**
  - **Prompt:** “Undo my Git mistake.”
  - **Route:** `recover-git-state` — needs the current state, intended target
    state, and work to preserve
  - **Rationale:** Git-state recovery is identifiable; safe execution needs the
    missing state details.
- **Nearby other-skill**
  - **Prompt:** “Cherry-pick commit abc123 onto the release branch.”
  - **Route:** `integrate-git-changes`
  - **Rationale:** Intended history integration, not recovery.
- **Unrelated negative**
  - **Prompt:** “Find the commit that first broke the login test.”
  - **Route:** `find-regression-commit`
  - **Rationale:** Regression bisection is explicitly excluded.
- **Ambiguous**
  - **Prompt:** “Reset main to the last good commit.”
  - **Route:** Clarification
  - **Rationale:** Need to establish local versus hosted state and whether the
    target is intentionally identified.
- **Composition**
  - **Prompt:** “Use bisect to identify the first regression, then restore my
    local branch to the last good state.”
  - **Route:** `find-regression-commit` + `recover-git-state`
  - **Rationale:** Bisection establishes the target; recovery changes local
    state.

## remove-legacy-compatibility

- **Direct positive**
  - **Prompt:** “Remove the deprecated v1 API alias after proving no supported
    client still calls it.”
  - **Route:** `remove-legacy-compatibility`
  - **Rationale:** Confirmed obsolete compatibility surface.
- **Paraphrased positive**
  - **Prompt:** “Trace consumers of this old shim and delete it only if they are
    gone.”
  - **Route:** `remove-legacy-compatibility`
  - **Rationale:** Consumer confirmation is the stated gate.
- **Incomplete relevant**
  - **Prompt:** “Clean up the old code.”
  - **Route:** `remove-legacy-compatibility` — needs the candidate compatibility
    surface and consumer evidence
  - **Rationale:** The “old” cleanup is plausibly this scope; confirmation is a
    required execution gate.
- **Nearby other-skill**
  - **Prompt:** “Migrate users from the old Node CLI to a Bun-based CLI.”
  - **Route:** `migrate-node-to-bun`
  - **Rationale:** Active migration is explicitly excluded.
- **Unrelated negative**
  - **Prompt:** “Fix a type error in the new payment handler.”
  - **Route:** No selection
  - **Rationale:** Routine implementation is not legacy removal.
- **Ambiguous**
  - **Prompt:** “Delete the old endpoint.”
  - **Route:** Clarification
  - **Rationale:** It might remain a supported contract; consumers and
    deprecation status are unknown.
- **Composition**
  - **Prompt:** “Update the migration docs, verify consumers are gone, then
    remove the compatibility shim.”
  - **Route:** `maintain-repository-docs` + `remove-legacy-compatibility`
  - **Rationale:** Documentation and confirmed surface removal are separate.

## replace-duckstation-textures

- **Direct positive**
  - **Prompt:** “Install and verify a DuckStation texture replacement for this
    exact NTSC-U PS1 game revision.”
  - **Route:** `replace-duckstation-textures`
  - **Rationale:** DuckStation PS1 texture work with revision control.
- **Paraphrased positive**
  - **Prompt:** “Dump the textures used by this specific PS1 build so I can
    create a replacement pack.”
  - **Route:** `replace-duckstation-textures`
  - **Rationale:** Texture dump/authoring workflow for DuckStation.
- **Incomplete relevant**
  - **Prompt:** “Replace these game textures in DuckStation.”
  - **Route:** `replace-duckstation-textures` — needs game revision and intended
    dump/create/install/verify action
  - **Rationale:** DuckStation texture work is explicit; identity and action are
    execution inputs.
- **Nearby other-skill**
  - **Prompt:** “Create a PNACH texture fix for PCSX2.”
  - **Route:** `write-pcsx2-patches`
  - **Rationale:** PCSX2 PNACH is not a DuckStation texture replacement;
    “texture fix” may need content clarification.
- **Unrelated negative**
  - **Prompt:** “Apply a GameShark cheat in DuckStation.”
  - **Route:** `apply-duckstation-patches`
  - **Rationale:** Cheats are explicitly excluded.
- **Ambiguous**
  - **Prompt:** “Make the PS1 game look better in the emulator.”
  - **Route:** Clarification
  - **Rationale:** Could mean textures, settings, patches, or a source build.
- **Composition**
  - **Prompt:** “Build DuckStation from the pinned revision, then install the
    texture pack for the matching game revision.”
  - **Route:** `compile-duckstation-from-source` +
    `replace-duckstation-textures`
  - **Rationale:** Source build and texture-pack work are separate scopes.

## replace-pcsx2-textures

- **Direct positive**
  - **Prompt:** “Create and verify a PCSX2 texture pack for this PS2 game's
    exact CRC and revision.”
  - **Route:** `replace-pcsx2-textures`
  - **Rationale:** Direct PCSX2 texture scope.
- **Paraphrased positive**
  - **Prompt:** “Dump the textures from this known PS2 CRC so I can replace the
    HUD art in PCSX2.”
  - **Route:** `replace-pcsx2-textures`
  - **Rationale:** PCSX2 texture dumping with required identity.
- **Incomplete relevant**
  - **Prompt:** “Install a PCSX2 texture pack.”
  - **Route:** `replace-pcsx2-textures` — needs game CRC/revision and pack
    identity
  - **Rationale:** PCSX2 texture installation is identifiable before its
    required validation inputs are supplied.
- **Nearby other-skill**
  - **Prompt:** “Write a PNACH code to change this PS2 game's widescreen
    behavior.”
  - **Route:** `write-pcsx2-patches`
  - **Rationale:** PNACH authoring, not textures.
- **Unrelated negative**
  - **Prompt:** “Replace DuckStation textures for a PS1 disc.”
  - **Route:** `replace-duckstation-textures`
  - **Rationale:** Wrong emulator/platform.
- **Ambiguous**
  - **Prompt:** “Fix the blurry PS2 HUD.”
  - **Route:** Clarification
  - **Rationale:** Could need a texture pack, emulator configuration, or a game
    patch.
- **Composition**
  - **Prompt:** “Compile PCSX2 from source and then verify the texture pack
    against its target CRC.”
  - **Route:** `compile-pcsx2-from-source` + `replace-pcsx2-textures`
  - **Rationale:** Build and texture verification are separate.

## review-software-security

- **Direct positive**
  - **Prompt:** “Threat-model the new file-upload service and identify
    exploitable trust-boundary failures.”
  - **Route:** `review-software-security`
  - **Rationale:** Defensive threat model and trust boundaries.
- **Paraphrased positive**
  - **Prompt:** “Review this dependency update for supply-chain and application
    security risk.”
  - **Route:** `review-software-security`
  - **Rationale:** Defensive dependency security review.
- **Incomplete relevant**
  - **Prompt:** “Check whether this is secure.”
  - **Route:** `review-software-security` — needs the target, trust boundary,
    threat model, and review depth
  - **Rationale:** A defensive security assessment is requested; missing scope
    limits execution, not initial selection.
- **Nearby other-skill**
  - **Prompt:** “Make the GitHub Actions release workflow stop exposing its
    token.”
  - **Route:** `develop-ci-pipelines` + `review-software-security`
  - **Rationale:** Pipeline repair and its security verification both apply.
- **Unrelated negative**
  - **Prompt:** “Obtain administrator access to the production host.”
  - **Route:** No selection
  - **Rationale:** Offensive/live-system access is outside defensive review
    scope.
- **Ambiguous**
  - **Prompt:** “Investigate the security incident.”
  - **Route:** Clarification
  - **Rationale:** Incident response is explicitly excluded; may instead require
    a post-incident review.
- **Composition**
  - **Prompt:** “Review PR #53's OAuth changes for trust-boundary flaws and
    submit the findings as review comments.”
  - **Route:** `review-software-security` + `manage-pull-requests`
  - **Rationale:** Security analysis and hosted review actions are distinct.

## run-duckstation

- **Direct positive**
  - **Prompt:** “Construct an isolated DuckStation command to boot this PS1 ISO
    with this BIOS and save directory.”
  - **Route:** `run-duckstation`
  - **Rationale:** Verified isolated DuckStation launch construction.
- **Paraphrased positive**
  - **Prompt:** “When authorized, launch this PS1 disc in DuckStation without
    touching my normal profile.”
  - **Route:** `run-duckstation`
  - **Rationale:** Isolated execution is directly described.
- **Incomplete relevant**
  - **Prompt:** “Run my game in DuckStation.”
  - **Route:** `run-duckstation` — needs media, build, authorization, and
    isolation details
  - **Rationale:** DuckStation launch is explicit; those inputs control safe
    execution.
- **Nearby other-skill**
  - **Prompt:** “Capture a reproducible DuckStation trace for the PS1 crash at
    the title screen.”
  - **Route:** `debug-duckstation`
  - **Rationale:** Guest debugging/capture is explicitly excluded.
- **Unrelated negative**
  - **Prompt:** “Compile the latest DuckStation source checkout.”
  - **Route:** `compile-duckstation-from-source`
  - **Rationale:** Build rather than launch.
- **Ambiguous**
  - **Prompt:** “Test this PS1 game in DuckStation.”
  - **Route:** Clarification
  - **Rationale:** Could mean ordinary launch, regression debugging, patch
    verification, or texture checking.
- **Composition**
  - **Prompt:** “Apply the verified PPF to an isolated PS1 profile, then launch
    the game in DuckStation.”
  - **Route:** `apply-duckstation-patches` + `run-duckstation`
  - **Rationale:** Patch setup and ordinary isolated launch.

## run-pcsx2

- **Direct positive**
  - **Prompt:** “Build an isolated PCSX2 launch command for this PS2 disc and
    separate save path.”
  - **Route:** `run-pcsx2`
  - **Rationale:** PCSX2 disc launch and data-path behavior.
- **Paraphrased positive**
  - **Prompt:** “When permitted, boot this PS2 ELF through PCSX2 without reusing
    my main emulator data.”
  - **Route:** `run-pcsx2`
  - **Rationale:** Isolated PCSX2 ELF execution.
- **Incomplete relevant**
  - **Prompt:** “Launch this in PCSX2.”
  - **Route:** `run-pcsx2` — needs target type, executable/build, authorization,
    and storage isolation
  - **Rationale:** PCSX2 launch is explicit; omitted details constrain execution
    only.
- **Nearby other-skill**
  - **Prompt:** “Debug the EE exception occurring after this PS2 ELF starts.”
  - **Route:** `debug-pcsx2`
  - **Rationale:** Guest debugging is explicitly excluded.
- **Unrelated negative**
  - **Prompt:** “Build PCSX2 from its pinned source commit.”
  - **Route:** `compile-pcsx2-from-source`
  - **Rationale:** Compilation, not launch.
- **Ambiguous**
  - **Prompt:** “Check whether the PS2 disc works in PCSX2.”
  - **Route:** Clarification
  - **Rationale:** Could be launch, regression debugging, texture validation, or
    patch verification.
- **Composition**
  - **Prompt:** “Create the matching PNACH for this CRC, then launch the PS2
    disc in an isolated PCSX2 profile.”
  - **Route:** `write-pcsx2-patches` + `run-pcsx2`
  - **Rationale:** Patch authoring plus isolated execution.

## sublime-plugin-development

- **Direct positive**
  - **Prompt:** “Fix this Sublime Text command so it owns its edit token
    correctly and survives package reload.”
  - **Route:** `sublime-plugin-development`
  - **Rationale:** Embedded Python command/edit and reload lifecycle.
- **Paraphrased positive**
  - **Prompt:** “Review the packed resource handling in this Sublime package.”
  - **Route:** `sublime-plugin-development`
  - **Rationale:** Sublime package resource scope.
- **Incomplete relevant**
  - **Prompt:** “Repair my Sublime plugin.”
  - **Route:** `sublime-plugin-development` — needs failing behavior and
    affected package component
  - **Rationale:** Sublime plugin work is identifiable before repair details.
- **Nearby other-skill**
  - **Prompt:** “Design one extension architecture that can support Sublime and
    VS Code.”
  - **Route:** `editor-extension-design`
  - **Rationale:** Cross-editor design, not selected-platform implementation.
- **Unrelated negative**
  - **Prompt:** “Implement a VS Code web extension command.”
  - **Route:** `vscode-extension-development`
  - **Rationale:** Different editor host.
- **Ambiguous**
  - **Prompt:** “Port this editor plugin to Sublime.”
  - **Route:** `editor-extension-design` — needs whether the result is a port
    plan; add `sublime-plugin-development` if implementation is requested
  - **Rationale:** Port planning is the initial route; concrete implementation
    is a separately scoped follow-on.
- **Composition**
  - **Prompt:** “Plan the cross-editor port, then implement the Sublime Text
    package's command layer.”
  - **Route:** `editor-extension-design` + `sublime-plugin-development`
  - **Rationale:** Design and Sublime-specific implementation.

## test-software-behavior

- **Direct positive**
  - **Prompt:** “Add a regression test proving malformed webhook payloads return
    400 without creating a record.”
  - **Route:** `test-software-behavior`
  - **Rationale:** Requested behavioral/regression evidence.
- **Paraphrased positive**
  - **Prompt:** “Diagnose why this integration test flakes only when the worker
    retries.”
  - **Route:** `test-software-behavior`
  - **Rationale:** Flaky-test diagnosis is explicit scope.
- **Incomplete relevant**
  - **Prompt:** “Improve the tests.”
  - **Route:** `test-software-behavior` — needs target behavior, regression, or
    flake symptom
  - **Rationale:** Testing is the requested outcome; the missing evidence
    determines the test work.
- **Nearby other-skill**
  - **Prompt:** “Repair the GitHub Actions job that never runs the test suite.”
  - **Route:** `develop-ci-pipelines`
  - **Rationale:** CI pipeline behavior, explicitly excluded here.
- **Unrelated negative**
  - **Prompt:** “Implement rate limiting for the API.”
  - **Route:** No selection
  - **Rationale:** Feature work alone does not invoke the testing skill.
- **Ambiguous**
  - **Prompt:** “Verify the new caching change.”
  - **Route:** Clarification
  - **Rationale:** It may request tests, routine test execution, benchmark
    evidence, or code review.
- **Composition**
  - **Prompt:** “Implement the cache eviction fix and add a regression test for
    the stale-read case.”
  - **Route:** `test-software-behavior`
  - **Rationale:** Testing is explicitly requested; no catalog route owns
    ordinary runtime implementation.

## vscode-extension-development

- **Direct positive**
  - **Prompt:** “Fix this VS Code extension so the command handles untrusted
    workspaces on web and desktop hosts.”
  - **Route:** `vscode-extension-development`
  - **Rationale:** VS Code Workspace Trust and host constraints.
- **Paraphrased positive**
  - **Prompt:** “Review URI handling in this remote VS Code extension activation
    path.”
  - **Route:** `vscode-extension-development`
  - **Rationale:** VS Code remote/URI lifecycle scope.
- **Incomplete relevant**
  - **Prompt:** “Repair the VS Code extension.”
  - **Route:** `vscode-extension-development` — needs failing behavior and
    target host
  - **Rationale:** VS Code extension work is explicit; host details guide
    execution.
- **Nearby other-skill**
  - **Prompt:** “Choose whether this extension should be built for VS Code or
    Zed.”
  - **Route:** `editor-extension-design`
  - **Rationale:** Editor-target selection is explicitly outside implementation
    scope.
- **Unrelated negative**
  - **Prompt:** “Fix the IntelliJ plugin's PSI threading violation.”
  - **Route:** `jetbrains-plugin-development`
  - **Rationale:** Different editor platform.
- **Ambiguous**
  - **Prompt:** “Port this editor extension to VS Code.”
  - **Route:** `editor-extension-design` — needs whether the result is a port
    plan; add `vscode-extension-development` if implementation is requested
  - **Rationale:** Port planning is the initial route; concrete implementation
    is a separately scoped follow-on.
- **Composition**
  - **Prompt:** “Design the migration from Zed to VS Code, then implement the VS
    Code web-host activation changes.”
  - **Route:** `editor-extension-design` + `vscode-extension-development`
  - **Rationale:** Port planning and target-specific work.

## write-pcsx2-patches

- **Direct positive**
  - **Prompt:** “Create a PNACH patch for this exact PS2 serial, CRC, region,
    and executable revision.”
  - **Route:** `write-pcsx2-patches`
  - **Rationale:** Direct PNACH request with required identity.
- **Paraphrased positive**
  - **Prompt:** “Verify that this PCSX2 cheat file matches the game's known CRC
    and PAL executable build.”
  - **Route:** `write-pcsx2-patches`
  - **Rationale:** PCSX2 patch verification.
- **Incomplete relevant**
  - **Prompt:** “Make a PCSX2 cheat.”
  - **Route:** `write-pcsx2-patches` — needs serial, CRC, region, executable
    revision, and desired effect
  - **Rationale:** PCSX2 cheat/PNACH work is identifiable; required identity
    details gate authoring.
- **Nearby other-skill**
  - **Prompt:** “Install a replacement HUD texture pack for this PS2 game.”
  - **Route:** `replace-pcsx2-textures`
  - **Rationale:** Texture replacements are explicitly excluded.
- **Unrelated negative**
  - **Prompt:** “Apply a DuckStation GameShark code to a PS1 game.”
  - **Route:** `apply-duckstation-patches`
  - **Rationale:** Wrong emulator/platform.
- **Ambiguous**
  - **Prompt:** “Fix the PS2 game's widescreen in PCSX2.”
  - **Route:** Clarification
  - **Rationale:** Could require PNACH, texture work, emulator launch settings,
    or guest debugging.
- **Composition**
  - **Prompt:** “Author the CRC-specific PNACH and then boot the disc in an
    isolated PCSX2 profile to verify it.”
  - **Route:** `write-pcsx2-patches` + `run-pcsx2`
  - **Rationale:** Patch creation plus isolated launch.

## zed-extension-development

- **Direct positive**
  - **Prompt:** “Repair this Zed extension's grammar asset and registry entry.”
  - **Route:** `zed-extension-development`
  - **Rationale:** Zed grammar and registry contracts.
- **Paraphrased positive**
  - **Prompt:** “Review the Rust/WASM API use in this Zed extension.”
  - **Route:** `zed-extension-development`
  - **Rationale:** Supported Zed Rust/WASM extension APIs.
- **Incomplete relevant**
  - **Prompt:** “Fix the Zed plugin.”
  - **Route:** `zed-extension-development` — needs extension type and failing
    behavior
  - **Rationale:** Zed extension work is explicit before its technical details
    are known.
- **Nearby other-skill**
  - **Prompt:** “Decide whether this language tool should target Zed, VS Code,
    or Neovim.”
  - **Route:** `editor-extension-design`
  - **Rationale:** Editor-selection/design task.
- **Unrelated negative**
  - **Prompt:** “Fix an Eclipse RCP target-platform dependency.”
  - **Route:** `eclipse-plugin-development`
  - **Rationale:** Different plugin platform.
- **Ambiguous**
  - **Prompt:** “Port our editor extension to Zed.”
  - **Route:** `editor-extension-design` — needs whether the result is a port
    plan; add `zed-extension-development` if implementation is requested
  - **Rationale:** Port planning is the initial route; concrete implementation
    is a separately scoped follow-on.
- **Composition**
  - **Prompt:** “Plan the VS Code-to-Zed port and implement the Zed WASM
    extension after the target contracts are decided.”
  - **Route:** `editor-extension-design` + `zed-extension-development`
  - **Rationale:** Planning and Zed implementation.

## Coordinator adjudication

Four corrected incomplete rows over-selected from domain-ambiguous requests. The
final interpretation below supersedes those rows, not their recorded reviewer
provenance:

- “Update the docs.” does not distinguish README, changelog, AGENTS.md, or
  external documentation. Inspect available context or clarify the document.
  Additional incomplete case: “Update this repository's README.” selects
  `maintain-repository-docs`; inspect its contents and the requested change.
- “Triage this report.” does not establish a hosted issue rather than a security
  incident or test report. Clarify the object. Additional incomplete case:
  “Triage this GitHub issue.” selects `manage-hosted-issues`; obtain its
  identity and triage criteria from available context.
- “Release version 2.4.” does not establish hosted publication rather than
  version selection, packaging, or tagging. Clarify the outcome. Additional
  incomplete case: “Publish the GitHub release.” selects
  `publish-hosted-releases`; determine the repository, tag, content, and assets.
- “Clean up the old code.” does not establish an obsolete compatibility path.
  Inspect the target or clarify the cleanup. Additional incomplete case: “Remove
  this obsolete compatibility shim.” selects `remove-legacy-compatibility`;
  verify consumers and the supported contract before removal.

These four additional cases are coordinator judgments, not new independent
reviewer runs. Known domain and goal permit selection before all execution
inputs exist; merely plausible domain is not enough. No metadata change was
needed to express these already documented boundaries.
