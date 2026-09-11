# First-half skill metadata routing evaluation

Scope: the first 20 directories in sorted `skills/*/SKILL.md`; all 40 `SKILL.md`
frontmatter entries and `agents/openai.yaml` files were considered as route
candidates. This is a metadata judgment exercise, not client-loader telemetry.
`format-github-markdown` and `interrogate-plan` are explicit-only.

## Correction note

Incomplete-relevant cases now state a known domain and task while omitting only
execution details. This separates selection from readiness to execute. The
normal local-commit case recognizes that repository inspection can infer routine
commit details; it does not universally require a supplied commit message.

Legend: **Clarify** means ask the stated question before selecting. **No
selection** means this catalog should not auto-select the named skill.

## apply-duckstation-patches

- **Direct positive**
  - Prompt: “Apply this PPF to the NTSC-U SLUS-01234 PS1 revision in an isolated
    DuckStation profile.”
  - Route: apply-duckstation-patches
  - Rationale: Exact PS1 revision and PPF patch.
- **Paraphrased positive**
  - Prompt: “Make these GameShark codes work for the PAL PlayStation build
    without changing my normal profile.”
  - Route: apply-duckstation-patches
  - Rationale: PS1 cheat work in an isolated profile.
- **Incomplete relevant**
  - Prompt: “Install this DuckStation cheat.”
  - Route: apply-duckstation-patches + clarify
  - Rationale: Need game revision and cheat material.
- **Nearby other-skill**
  - Prompt: “Write a PNACH for this PS2 game CRC.”
  - Route: write-pcsx2-patches
  - Rationale: PNACH is PCSX2-only.
- **Unrelated negative**
  - Prompt: “Explain how to poach an egg.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Patch my game so the bug goes away.”
  - Route: Clarify
  - Rationale: Need platform and whether patching or debugging is wanted.
- **Composition**
  - Prompt: “Apply this PS1 PPF and document the verified change in the
    changelog.”
  - Route: apply-duckstation-patches + maintain-changelog
  - Rationale: Patch verification and documentation are distinct.

## commit-git-changes

- **Direct positive**
  - Prompt: “Create one local commit for src/parser.ts and leave every other
    change alone.”
  - Route: commit-git-changes
  - Rationale: Focused local commit.
- **Paraphrased positive**
  - Prompt: “Snapshot only the intended hunks as a Git commit and keep my WIP
    unstaged.”
  - Route: commit-git-changes
  - Rationale: Same local-commit outcome.
- **Incomplete relevant**
  - Prompt: “Commit my current changes.”
  - Route: commit-git-changes
  - Rationale: Inspect status, diff, and staging to infer routine scope; clarify
    only competing intent.
- **Nearby other-skill**
  - Prompt: “Rebase my feature branch onto main and resolve conflicts.”
  - Route: integrate-git-changes
  - Rationale: This is history integration.
- **Unrelated negative**
  - Prompt: “What is the capital of Estonia?”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Get these changes into main.”
  - Route: Clarify
  - Rationale: Could mean local integration or a hosted PR merge.
- **Composition**
  - Prompt: “Commit the selected files locally, then open a pull request.”
  - Route: commit-git-changes + manage-pull-requests
  - Rationale: Local commit and hosted PR are separate.

## compile-duckstation-from-source

- **Direct positive**
  - Prompt: “Compile DuckStation from commit abc123 on Linux and show artifact
    evidence.”
  - Route: compile-duckstation-from-source
  - Rationale: Pinned source compilation.
- **Paraphrased positive**
  - Prompt: “Build a DuckStation executable from this checked-out revision with
    dependencies.”
  - Route: compile-duckstation-from-source
  - Rationale: Same source-build outcome.
- **Incomplete relevant**
  - Prompt: “Build DuckStation.”
  - Route: compile-duckstation-from-source + clarify
  - Rationale: Need checkout or revision and target platform.
- **Nearby other-skill**
  - Prompt: “Launch this PS1 ISO with my DuckStation build in an isolated
    profile.”
  - Route: run-duckstation
  - Rationale: Launching is not compiling.
- **Unrelated negative**
  - Prompt: “Rename the photos in this folder.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Get DuckStation running on macOS.”
  - Route: Clarify / no catalog selection
  - Rationale: Could mean release installation or source compilation.
- **Composition**
  - Prompt: “Compile DuckStation from this pin, then launch a PS1 disc with it.”
  - Route: compile-duckstation-from-source + run-duckstation
  - Rationale: Build and launch are distinct.

## compile-pcsx2-from-source

- **Direct positive**
  - Prompt: “Compile PCSX2 from tag v2.1.0 on Linux and retain resource
    evidence.”
  - Route: compile-pcsx2-from-source
  - Rationale: Pinned PCSX2 source compilation.
- **Paraphrased positive**
  - Prompt: “Produce a PCSX2 executable from this exact checkout with
    dependencies.”
  - Route: compile-pcsx2-from-source
  - Rationale: Same source-build outcome.
- **Incomplete relevant**
  - Prompt: “Build PCSX2.”
  - Route: compile-pcsx2-from-source + clarify
  - Rationale: Need checkout or revision and target platform.
- **Nearby other-skill**
  - Prompt: “Run this PS2 ELF with PCSX2 in an isolated data directory.”
  - Route: run-pcsx2
  - Rationale: Launching is not compiling.
- **Unrelated negative**
  - Prompt: “Convert this CSV to JSON.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Install PCSX2 on Windows.”
  - Route: No selection
  - Rationale: Release-binary installation is excluded and unclaimed.
- **Composition**
  - Prompt: “Compile PCSX2 from this pin, then boot this PS2 disc with it.”
  - Route: compile-pcsx2-from-source + run-pcsx2
  - Rationale: Build and launch are distinct.

## configure-hosted-repositories

- **Direct positive**
  - Prompt: “Require two reviews before merge on this GitHub main branch.”
  - Route: configure-hosted-repositories
  - Rationale: Hosted branch protection.
- **Paraphrased positive**
  - Prompt: “Block direct pushes to the production branch in GitLab settings.”
  - Route: configure-hosted-repositories
  - Rationale: Hosted project protection.
- **Incomplete relevant**
  - Prompt: “Enable required status checks for this GitHub repository.”
  - Route: configure-hosted-repositories + clarify
  - Rationale: Need repository, branch, and check names.
- **Nearby other-skill**
  - Prompt: “Add a GitHub Actions workflow that tests pull requests.”
  - Route: develop-ci-pipelines
  - Rationale: Pipeline files are excluded.
- **Unrelated negative**
  - Prompt: “Calculate 17 percent of 440.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Lock the repository before the release.”
  - Route: Clarify
  - Rationale: Could mean protections, workflow, or publication.
- **Composition**
  - Prompt: “Protect release tags in GitHub, then publish v2.0.”
  - Route: configure-hosted-repositories + publish-hosted-releases
  - Rationale: Protection and publication differ.

## configure-repository-governance

- **Direct positive**
  - Prompt: “Create CODEOWNERS and issue templates using GitHub rules.”
  - Route: configure-repository-governance
  - Rationale: Governance files and provider rules.
- **Paraphrased positive**
  - Prompt: “Add a contributor policy and pull-request template.”
  - Route: configure-repository-governance
  - Rationale: Repository governance artifacts.
- **Incomplete relevant**
  - Prompt: “Add a CODEOWNERS file for this repository.”
  - Route: configure-repository-governance + clarify
  - Rationale: Need ownership rules, directory boundaries, and provider.
- **Nearby other-skill**
  - Prompt: “Require signed commits and two reviews in GitHub settings.”
  - Route: configure-hosted-repositories
  - Rationale: Hosted settings are excluded.
- **Unrelated negative**
  - Prompt: “Summarize this novel.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Make pull requests require an owner approval.”
  - Route: Clarify
  - Rationale: CODEOWNERS and hosted enforcement may both be needed.
- **Composition**
  - Prompt: “Add CODEOWNERS and write the CONTRIBUTING ownership guide.”
  - Route: configure-repository-governance + maintain-repository-docs
  - Rationale: Governance file and documentation differ.

## debug-duckstation

- **Direct positive**
  - Prompt: “Capture a reproducible DuckStation trace for this PS1 regression.”
  - Route: debug-duckstation
  - Rationale: PS1 guest debugging.
- **Paraphrased positive**
  - Prompt: “Collect evidence for why this PlayStation title crashes in
    DuckStation.”
  - Route: debug-duckstation
  - Rationale: Guest failure diagnosis.
- **Incomplete relevant**
  - Prompt: “DuckStation is broken for this game.”
  - Route: debug-duckstation + clarify
  - Rationale: Need game revision, symptom, and reproduction.
- **Nearby other-skill**
  - Prompt: “Boot this PS1 ISO in DuckStation without debugging it.”
  - Route: run-duckstation
  - Rationale: Ordinary launch.
- **Unrelated negative**
  - Prompt: “Make a birthday invitation.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “My PS1 cheat does not work in DuckStation.”
  - Route: Clarify
  - Rationale: Could be patch application or emulator debugging.
- **Composition**
  - Prompt: “Reproduce this DuckStation regression and bisect its first bad
    commit.”
  - Route: debug-duckstation + find-regression-commit
  - Rationale: Capture and Git bisect differ.

## debug-pcsx2

- **Direct positive**
  - Prompt: “Collect a reproducible PCSX2 EE crash trace for this PS2 game.”
  - Route: debug-pcsx2
  - Rationale: PCSX2 guest debugging.
- **Paraphrased positive**
  - Prompt: “Find evidence for this PS2 IOP emulation regression.”
  - Route: debug-pcsx2
  - Rationale: IOP guest diagnosis.
- **Incomplete relevant**
  - Prompt: “PCSX2 crashes for this PS2 title.”
  - Route: debug-pcsx2 + clarify
  - Rationale: Need title revision, environment, and reproduction.
- **Nearby other-skill**
  - Prompt: “Create a PNACH for PS2 CRC 1234ABCD.”
  - Route: write-pcsx2-patches
  - Rationale: PNACH authoring is excluded.
- **Unrelated negative**
  - Prompt: “Order three office chairs.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “My PS2 patch does not fix the problem.”
  - Route: Clarify
  - Rationale: Could be PNACH data or an emulation defect.
- **Composition**
  - Prompt: “Capture the PCSX2 regression and identify its first bad commit.”
  - Route: debug-pcsx2 + find-regression-commit
  - Rationale: Capture and Git bisect differ.

## design-software-boundaries

- **Direct positive**
  - Prompt: “Choose ownership and public contracts while splitting this monolith
    into packages.”
  - Route: design-software-boundaries
  - Rationale: Architecture and structural migration.
- **Paraphrased positive**
  - Prompt: “Review service dependency direction before the package split.”
  - Route: design-software-boundaries
  - Rationale: Boundary review.
- **Incomplete relevant**
  - Prompt: “Split the monolithic billing package into API and implementation
    packages.”
  - Route: design-software-boundaries + clarify
  - Rationale: Need ownership, contract, and dependency constraints.
- **Nearby other-skill**
  - Prompt: “Add validation to the existing endpoint without changing
    boundaries.”
  - Route: No selection
  - Rationale: Routine implementation is excluded.
- **Unrelated negative**
  - Prompt: “Translate this sentence into Finnish.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Move the controller into its own module.”
  - Route: Clarify
  - Rationale: Could be routine extraction or a boundary change.
- **Composition**
  - Prompt: “Redesign package boundaries and remove a consumer-free
    compatibility facade.”
  - Route: design-software-boundaries + remove-legacy-compatibility
  - Rationale: Design and proven removal differ.

## develop-ci-pipelines

- **Direct positive**
  - Prompt: “Repair this GitHub Actions workflow so integration tests run on
    pull requests.”
  - Route: develop-ci-pipelines
  - Rationale: GitHub Actions behavior.
- **Paraphrased positive**
  - Prompt: “Review GitLab CI deployment access to protected variables from
    merge requests.”
  - Route: develop-ci-pipelines
  - Rationale: CI trust-boundary review.
- **Incomplete relevant**
  - Prompt: “Our GitHub Actions test workflow fails on pull requests.”
  - Route: develop-ci-pipelines + clarify
  - Rationale: Need failing run, logs, workflow, and expected behavior.
- **Nearby other-skill**
  - Prompt: “Require successful checks before GitHub merges.”
  - Route: configure-hosted-repositories
  - Rationale: Hosted protection setting.
- **Unrelated negative**
  - Prompt: “Plan a weekend hike.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Release automation is broken.”
  - Route: Clarify
  - Rationale: Could be CI workflow or hosted-release action.
- **Composition**
  - Prompt: “Fix the release workflow and publish its artifact as a hosted
    release.”
  - Route: develop-ci-pipelines + publish-hosted-releases
  - Rationale: Automation and hosted mutation differ.

## eclipse-plugin-development

- **Direct positive**
  - Prompt: “Repair this Eclipse RCP plug-in OSGi activation and target
    dependency.”
  - Route: eclipse-plugin-development
  - Rationale: Eclipse lifecycle and target platform.
- **Paraphrased positive**
  - Prompt: “Fix this PDE extension-point registration so the Eclipse package
    loads.”
  - Route: eclipse-plugin-development
  - Rationale: Eclipse plugin integration.
- **Incomplete relevant**
  - Prompt: “Repair OSGi activation in this Eclipse RCP plug-in.”
  - Route: eclipse-plugin-development + clarify
  - Rationale: Need target platform, dependencies, and failure evidence.
- **Nearby other-skill**
  - Prompt: “Fix PSI threading in an IntelliJ Platform plugin.”
  - Route: jetbrains-plugin-development
  - Rationale: IntelliJ-specific contract.
- **Unrelated negative**
  - Prompt: “Sort these names alphabetically.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Add language support as an IDE plugin.”
  - Route: Clarify
  - Rationale: Editor target is unspecified.
- **Composition**
  - Prompt: “Plan an Eclipse-to-VS-Code port, then implement the VS Code
    extension.”
  - Route: editor-extension-design + vscode-extension-development
  - Rationale: Port planning and implementation differ.

## editor-extension-design

- **Direct positive**
  - Prompt: “Choose VS Code, Zed, or Neovim for this extension and design
    portability.”
  - Route: editor-extension-design
  - Rationale: Target choice and cross-editor design.
- **Paraphrased positive**
  - Prompt: “Plan a Sublime package port to Zed without implementing it.”
  - Route: editor-extension-design
  - Rationale: Extension-port planning.
- **Incomplete relevant**
  - Prompt: “Design a cross-editor extension port for this Sublime package.”
  - Route: editor-extension-design + clarify
  - Rationale: Need destination editors and portability constraints.
- **Nearby other-skill**
  - Prompt: “Implement this already-designed VS Code extension change.”
  - Route: vscode-extension-development
  - Rationale: Existing-target implementation is excluded.
- **Unrelated negative**
  - Prompt: “Explain quicksort.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Add a command to our plugin.”
  - Route: Clarify
  - Rationale: Editor and design versus implementation are unknown.
- **Composition**
  - Prompt: “Choose an editor and, if VS Code wins, implement the feature
    there.”
  - Route: editor-extension-design + vscode-extension-development
  - Rationale: Decision and target implementation differ.

## find-regression-commit

- **Direct positive**
  - Prompt: “Bisect and verify the first commit that caused this reproducible
    regression.”
  - Route: find-regression-commit
  - Rationale: First-introducing-commit search.
- **Paraphrased positive**
  - Prompt: “Set up a trustworthy Git bisect for when this passing behavior
    first failed.”
  - Route: find-regression-commit
  - Rationale: Reproducible good/bad oracle.
- **Incomplete relevant**
  - Prompt: “Find the bad commit for this reproducible failing test.”
  - Route: find-regression-commit + clarify
  - Rationale: Need good/bad range and oracle command.
- **Nearby other-skill**
  - Prompt: “Undo the regression commit while preserving other work.”
  - Route: recover-git-state
  - Rationale: Restore/revert, not search.
- **Unrelated negative**
  - Prompt: “Suggest a team name.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “The last release is broken; tell me which commit did it.”
  - Route: Clarify
  - Rationale: May lack a reproducible oracle and need debugging.
- **Composition**
  - Prompt: “Capture a DuckStation failure, then bisect its first bad source
    commit.”
  - Route: debug-duckstation + find-regression-commit
  - Rationale: Capture and history search differ.

## format-github-markdown

- **Direct positive**
  - Prompt: “$format-github-markdown Normalize this README and run
    markdownlint-cli2.”
  - Route: format-github-markdown
  - Rationale: Explicit invocation satisfies policy.
- **Paraphrased positive**
  - Prompt: “Normalize this GFM file and make markdownlint-cli2 pass.”
  - Route: No automatic selection
  - Rationale: Explicit-only policy prohibits implicit activation.
- **Incomplete relevant**
  - Prompt: “Fix README Markdown lint.”
  - Route: No automatic selection
  - Rationale: Explicit-only policy still applies.
- **Nearby other-skill**
  - Prompt: “Write a CONTRIBUTING guide from actual repository commands.”
  - Route: maintain-repository-docs
  - Rationale: Content outcome, not explicit formatting.
- **Unrelated negative**
  - Prompt: “What time is it in Tokyo?”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Clean up the Markdown docs.”
  - Route: No automatic selection
  - Rationale: Could mean content changes; no explicit invocation.
- **Composition**
  - Prompt: “$format-github-markdown lint this README, then rewrite setup
    instructions.”
  - Route: format-github-markdown + maintain-repository-docs
  - Rationale: Explicit formatting plus documentation revision.

## integrate-git-changes

- **Direct positive**
  - Prompt: “Rebase my feature branch onto main, preserve dirty work, and
    resolve conflicts.”
  - Route: integrate-git-changes
  - Rationale: Local rebase and integration.
- **Paraphrased positive**
  - Prompt: “Cherry-pick these two commits into the release branch without
    losing WIP.”
  - Route: integrate-git-changes
  - Rationale: Local history integration.
- **Incomplete relevant**
  - Prompt: “Rebase this feature branch onto main.”
  - Route: integrate-git-changes + clarify
  - Rationale: Need intended upstream and conflict behavior; inspect worktree
    for unrelated work.
- **Nearby other-skill**
  - Prompt: “Create a local commit from these selected hunks.”
  - Route: commit-git-changes
  - Rationale: Routine local commit.
- **Unrelated negative**
  - Prompt: “Find the median of these numbers.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Bring the PR changes into my local branch.”
  - Route: integrate-git-changes + clarify
  - Rationale: Local integration is indicated but source method is unknown.
- **Composition**
  - Prompt: “Rebase onto main, resolve conflicts, and commit the intended fix.”
  - Route: integrate-git-changes + commit-git-changes
  - Rationale: Integration and follow-up commit differ.

## interrogate-plan

- **Direct positive**
  - Prompt: “$interrogate-plan Challenge this migration plan until risks are
    explicit.”
  - Route: interrogate-plan
  - Rationale: Explicit invocation satisfies policy.
- **Paraphrased positive**
  - Prompt: “Review this plan for contradictions, assumptions, and risks.”
  - Route: No automatic selection
  - Rationale: Explicit-only policy prohibits implicit activation.
- **Incomplete relevant**
  - Prompt: “Is this supplied migration plan internally consistent?”
  - Route: No automatic selection
  - Rationale: Explicit-only policy still applies.
- **Nearby other-skill**
  - Prompt: “Implement the approved migration plan.”
  - Route: No selection
  - Rationale: This skill does not implement plans.
- **Unrelated negative**
  - Prompt: “What is a semaphore?”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “What is missing from this plan?”
  - Route: No automatic selection
  - Rationale: No explicit invocation.
- **Composition**
  - Prompt: “$interrogate-plan expose package-split risks, then decide
    ownership.”
  - Route: interrogate-plan + design-software-boundaries
  - Rationale: Plan interrogation and boundary decision differ.

## jetbrains-plugin-development

- **Direct positive**
  - Prompt: “Fix this IntelliJ plugin PSI access from a background thread and
    descriptor compatibility.”
  - Route: jetbrains-plugin-development
  - Rationale: IntelliJ PSI, threading, and compatibility.
- **Paraphrased positive**
  - Prompt: “Repair our Rider plug-in lifecycle for its declared target IDE
    version.”
  - Route: jetbrains-plugin-development
  - Rationale: JetBrains plugin lifecycle.
- **Incomplete relevant**
  - Prompt: “Repair this IntelliJ plugin dependency declaration.”
  - Route: jetbrains-plugin-development + clarify
  - Rationale: Need target IDE, dependency details, and failure evidence.
- **Nearby other-skill**
  - Prompt: “Fix a VS Code extension Workspace Trust behavior.”
  - Route: vscode-extension-development
  - Rationale: VS Code host/trust scope.
- **Unrelated negative**
  - Prompt: “Create a grocery list.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “The editor plugin crashes on startup.”
  - Route: Clarify
  - Rationale: Could be any supported editor ecosystem.
- **Composition**
  - Prompt: “Plan an IntelliJ-to-VS-Code port and implement the VS Code host
    integration.”
  - Route: editor-extension-design + vscode-extension-development
  - Rationale: Port planning and destination implementation differ.

## maintain-agent-skills

- **Direct positive**
  - Prompt: “Audit these Agent Skill packages against the current
    specification.”
  - Route: maintain-agent-skills
  - Rationale: Skill-package audit.
- **Paraphrased positive**
  - Prompt: “Split this oversized agent skill and validate the resulting
    packages.”
  - Route: maintain-agent-skills
  - Rationale: Skill split and validation.
- **Incomplete relevant**
  - Prompt: “Update this Agent Skill package routing metadata.”
  - Route: maintain-agent-skills + clarify
  - Rationale: Need package, requested change, and authoritative sources.
- **Nearby other-skill**
  - Prompt: “Create scoped AGENTS.md instructions for the monorepo.”
  - Route: maintain-agents-md
  - Rationale: AGENTS.md is excluded.
- **Unrelated negative**
  - Prompt: “Make this logo blue.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Tune the agent instructions.”
  - Route: Clarify
  - Rationale: Could be a skill, AGENTS.md, or provider persona.
- **Composition**
  - Prompt: “Update this Agent Skill and revise its README for the new
    workflow.”
  - Route: maintain-agent-skills + maintain-repository-docs
  - Rationale: Package and repository docs differ.

## maintain-agents-md

- **Direct positive**
  - Prompt: “Derive root AGENTS.md and docs/AGENTS.md from repository
    workflows.”
  - Route: maintain-agents-md
  - Rationale: Scoped AGENTS.md authoring.
- **Paraphrased positive**
  - Prompt: “Audit whether this nested AGENTS.md has the right evidence and
    scope.”
  - Route: maintain-agents-md
  - Rationale: AGENTS.md scope audit.
- **Incomplete relevant**
  - Prompt: “Derive AGENTS.md guidance for the src/ directory.”
  - Route: maintain-agents-md + clarify
  - Rationale: Need scope and workflows that ground the guidance.
- **Nearby other-skill**
  - Prompt: “Rewrite the README setup section from executable project evidence.”
  - Route: maintain-repository-docs
  - Rationale: General docs are excluded.
- **Unrelated negative**
  - Prompt: “Generate a random password.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Write agent instructions for GitHub.”
  - Route: Clarify
  - Rationale: Could be AGENTS.md or excluded custom-agent persona.
- **Composition**
  - Prompt: “Derive AGENTS.md guidance and audit its referenced Agent Skill.”
  - Route: maintain-agents-md + maintain-agent-skills
  - Rationale: Repository instructions and skill package differ.

## maintain-changelog

- **Direct positive**
  - Prompt: “Audit CHANGELOG.md and decide whether 2.0.0 is valid next SemVer.”
  - Route: maintain-changelog
  - Rationale: Changelog validation and SemVer decision.
- **Paraphrased positive**
  - Prompt: “Normalize these release notes and check the version number.”
  - Route: maintain-changelog
  - Rationale: Release-note and SemVer work.
- **Incomplete relevant**
  - Prompt: “Prepare v2.0 release notes from these listed changes.”
  - Route: maintain-changelog + clarify
  - Rationale: Need final version decision and release-note audience.
- **Nearby other-skill**
  - Prompt: “Publish existing v2.0.0 notes and assets as a GitHub release.”
  - Route: publish-hosted-releases
  - Rationale: Hosted release publication is excluded.
- **Unrelated negative**
  - Prompt: “Show today’s weather.”
  - Route: No selection
  - Rationale: Outside the catalog.
- **Ambiguous**
  - Prompt: “Release version 2.0 now.”
  - Route: Clarify
  - Rationale: Could mean SemVer, hosted publication, or local tagging.
- **Composition**
  - Prompt: “Write verified v2.0 release notes, then publish the GitHub
    release.”
  - Route: maintain-changelog + publish-hosted-releases
  - Rationale: Notes and hosted mutation differ.

## Metadata findings

1. **Medium — release-binary emulator installation is an uncovered candidate
   workflow.** The frontmatter in
   `skills/compile-duckstation-from-source/SKILL.md` and
   `skills/compile-pcsx2-from-source/SKILL.md` explicitly excludes
   release-binary installation. `run-duckstation` and `run-pcsx2` cover launch
   construction, not installation, and no other catalog description claims it.
   Therefore “Install PCSX2 on Windows” and “Get DuckStation running on macOS”
   have no selection. This is coverage evidence for a domain-workflow review,
   not a conclusion that a new installation micro-skill is required.

2. **Low — ordinary wording is intentionally unroutable for two otherwise
   matching capabilities.** `skills/format-github-markdown/agents/openai.yaml`
   and `skills/interrogate-plan/agents/openai.yaml` set
   `policy.allow_implicit_invocation: false`. Clear ordinary requests to make
   markdownlint pass or challenge a plan’s assumptions therefore do not
   auto-select them. This is correct if explicit-only behavior is deliberate;
   otherwise it is a discoverability/routing gap demonstrated above.

No other concrete misrouting, missing capability, or harmful fragmentation was
identified from metadata. Hosted settings/governance/issue/PR/release work,
local Git operations, emulator lifecycle tasks, and editor design versus
editor-specific implementation have explicit, coherent boundaries.
