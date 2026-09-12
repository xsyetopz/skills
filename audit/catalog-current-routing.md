# Current catalog routing audit

## Scope and method

This is a metadata and named-invocation classification review of all 30 current
skill packages. It is not a client-loader activation or execution test. Initial
routes were classified from each `SKILL.md` frontmatter and
`agents/openai.yaml`, before any skill body was read. The body pass then checked
execution boundaries only.

The OpenAI metadata marks 28 packages with `allow_implicit_invocation: false`.
The remaining two packages, `design-software-boundaries` and
`editor-extension-design`, omit that policy and their descriptions/bodies permit
implicit planning selection. For explicit-only packages, a bare semantic match
is intentionally not a route; explicit invocation by name is required (the
examples use `$skill-name`). An explicit but under-specified request selects the
skill but is not execution-ready. Routes below are reviewer classifications, not
observed client activations.

Body checks found the named-invocation contract repeated in every explicit-only
package. The two implicit planning packages retain their metadata boundary.
Integration found incorrect reviewer classifications in several adjacent cases;
the coordinator corrections below supersede those entries.

## Per-package routes

### `compile-duckstation-from-source`

- **Direct**
  - Prompt: “Use $compile-duckstation-from-source to build a pinned DuckStation
    checkout into a reproducible executable.”
  - Route: `compile-duckstation-from-source`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Build DuckStation from this checkout and record the artifact hash.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $compile-duckstation-from-source to Compile DuckStation, but no
    checkout, revision, or platform is supplied.”
  - Route: `compile-duckstation-from-source`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $operate-duckstation to launch an already built DuckStation
    executable with an isolated profile.”
  - Route: `operate-duckstation`
  - Reason: Launch-time operation is adjacent to, but distinct from, source
    compilation.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Prepare this emulator task”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $compile-duckstation-from-source to build a pinned
    DuckStation checkout into a reproducible executable, then use
    $operate-duckstation
    for the related follow-up.”
  - Route: `compile-duckstation-from-source`, then `operate-duckstation`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `compile-pcsx2-from-source`

- **Direct**
  - Prompt: “Use $compile-pcsx2-from-source to build a pinned PCSX2 checkout
    into a reproducible executable.”
  - Route: `compile-pcsx2-from-source`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Build PCSX2 from this checkout and retain packaged-resource
    evidence.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $compile-pcsx2-from-source to Compile PCSX2, but no checkout,
    revision, or platform is supplied.”
  - Route: `compile-pcsx2-from-source`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $compile-duckstation-from-source to handle a DuckStation source
    build.”
  - Route: `compile-duckstation-from-source`
  - Reason: The requested adjacent capability is outside
    `compile-pcsx2-from-source`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Prepare this emulator task”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $compile-pcsx2-from-source to build a pinned PCSX2
    checkout into a reproducible executable, then use $operate-pcsx2
    for the related follow-up.”
  - Route: `compile-pcsx2-from-source`, then `operate-pcsx2`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `configure-repository-governance`

- **Direct**
  - Prompt: “Use $configure-repository-governance to add or audit repository
    governance files.”
  - Route: `configure-repository-governance`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add CODEOWNERS and a pull-request template from the provider
    rules.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $configure-repository-governance to Create governance files,
    but the provider and requested policy are absent.”
  - Route: `configure-repository-governance`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $manage-hosted-repositories to handle a hosted
    branch-protection setting.”
  - Route: `manage-hosted-repositories`
  - Reason: The requested adjacent capability is outside
    `configure-repository-governance`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Improve repository policy”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $configure-repository-governance to add or audit
    repository governance files, then use $develop-ci-pipelines
    for the related follow-up.”
  - Route: `configure-repository-governance`, then `develop-ci-pipelines`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `design-software-boundaries`

- **Direct**
  - Prompt: “Choose a module ownership and dependency boundary.”
  - Route: `design-software-boundaries`
  - Reason: in-scope planning route permits implicit selection.
- **Paraphrased**
  - Prompt: “Should this service split its billing module from its HTTP
    transport?”
  - Route: `design-software-boundaries`
  - Reason: paraphrase retains the planning goal.
- **Incomplete**
  - Prompt: “Use $design-software-boundaries to Design a new package boundary,
    but the consumers and failure ownership are unknown.”
  - Route: `design-software-boundaries`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $interrogate-plan to question unresolved assumptions in this
    supplied architecture plan without implementing it.”
  - Route: `interrogate-plan`
  - Reason: Sustained plan interrogation is distinct from choosing the
    architecture.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Make this codebase cleaner”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Choose a module ownership and dependency boundary, then use
    $interrogate-plan for the related implementation.”
  - Route: `design-software-boundaries`, then `interrogate-plan`
  - Reason: planning selects implicitly; the implementation route is explicitly
    named.

### `develop-ci-pipelines`

- **Direct**
  - Prompt: “Use $develop-ci-pipelines to repair or review a CI pipeline.”
  - Route: `develop-ci-pipelines`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Fix the GitHub Actions workflow that skips its test job on pull
    requests.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $develop-ci-pipelines to Repair this pipeline, but the
    provider, event, and failing transition are unknown.”
  - Route: `develop-ci-pipelines`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $manage-hosted-repositories to handle a hosted repository
    setting.”
  - Route: `manage-hosted-repositories`
  - Reason: The requested adjacent capability is outside `develop-ci-pipelines`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Make automation reliable”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $develop-ci-pipelines to repair or review a CI
    pipeline, then use $test-software-behavior
    for the related follow-up.”
  - Route: `develop-ci-pipelines`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `eclipse-plugin-development`

- **Direct**
  - Prompt: “Use $eclipse-plugin-development to build, repair, or review an
    Eclipse plug-in.”
  - Route: `eclipse-plugin-development`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add an Eclipse command handler and preserve its OSGi lifecycle.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $eclipse-plugin-development to Repair this Eclipse plug-in, but
    its target platform and bundles are unknown.”
  - Route: `eclipse-plugin-development`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $jetbrains-plugin-development to handle a JetBrains plug-in.”
  - Route: `jetbrains-plugin-development`
  - Reason: The requested adjacent capability is outside
    `eclipse-plugin-development`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Fix this IDE extension”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $eclipse-plugin-development to build, repair, or
    review an Eclipse plug-in, then use $test-software-behavior
    for the related follow-up.”
  - Route: `eclipse-plugin-development`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `editor-extension-design`

- **Direct**
  - Prompt: “Choose an editor host or plan a cross-editor extension.”
  - Route: `editor-extension-design`
  - Reason: in-scope planning route permits implicit selection.
- **Paraphrased**
  - Prompt: “Which editor hosts can support this shared formatter extension?”
  - Route: `editor-extension-design`
  - Reason: paraphrase retains the planning goal.
- **Incomplete**
  - Prompt: “Use $editor-extension-design to Plan an editor port, but the source
    and target hosts are unspecified.”
  - Route: `editor-extension-design`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $vscode-extension-development to handle implementation in an
    already selected editor.”
  - Route: `vscode-extension-development`
  - Reason: The requested adjacent capability is outside
    `editor-extension-design`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Make this editor extension portable”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Choose an editor host or plan a cross-editor extension, then use
    $design-software-boundaries for the related implementation.”
  - Route: `editor-extension-design`, then `design-software-boundaries`
  - Reason: planning selects implicitly; the implementation route is explicitly
    named.

### `find-regression-commit`

- **Direct**
  - Prompt: “Use $find-regression-commit to identify the first commit for a
    reproducible regression.”
  - Route: `find-regression-commit`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Bisect this reproducible failure between known good and bad
    revisions.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $find-regression-commit to Find the regression commit, but
    neither an oracle nor good/bad boundaries are supplied.”
  - Route: `find-regression-commit`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $test-software-behavior to add a regression test for this
    reproduced defect; do not search Git history.”
  - Route: `test-software-behavior`
  - Reason: Behavioral regression coverage does not require commit bisection.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Find what broke”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $find-regression-commit to identify the first
    commit for a reproducible regression, then use $manage-git-state
    for the related follow-up.”
  - Route: `find-regression-commit`, then `manage-git-state`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `format-github-markdown`

- **Direct**
  - Prompt: “Use $format-github-markdown to format or lint selected GitHub
    Flavored Markdown.”
  - Route: `format-github-markdown`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Normalize this Markdown file and make its lint diagnostics pass.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $format-github-markdown to Format Markdown, but no target file
    or repository root is identified.”
  - Route: `format-github-markdown`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $maintain-repository-docs to handle document content
    decisions.”
  - Route: `maintain-repository-docs`
  - Reason: The requested adjacent capability is outside
    `format-github-markdown`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Improve these docs”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $format-github-markdown to format or lint selected
    GitHub Flavored Markdown, then use $maintain-changelog
    for the related follow-up.”
  - Route: `format-github-markdown`, then `maintain-changelog`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `interrogate-plan`

- **Direct**
  - Prompt: “Use $interrogate-plan to question a supplied plan until its
    decisions and risks are explicit.”
  - Route: `interrogate-plan`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Challenge this rollout plan for contradictions and missing
    decisions.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $interrogate-plan to Interrogate this plan, but no plan or
    requirements artifact is supplied.”
  - Route: `interrogate-plan`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $design-software-boundaries to choose module ownership for this
    application.”
  - Route: `design-software-boundaries`
  - Reason: Architecture selection is distinct from questioning a supplied plan.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Help me decide”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $interrogate-plan to question a supplied plan until
    its decisions and risks are explicit, then use
    $review-software-security
    for the related follow-up.”
  - Route: `interrogate-plan`, then `review-software-security`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `jetbrains-plugin-development`

- **Direct**
  - Prompt: “Use $jetbrains-plugin-development to build, repair, or review an
    IntelliJ Platform plug-in.”
  - Route: `jetbrains-plugin-development`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add a PSI action to this IntelliJ plug-in and preserve threading
    rules.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $jetbrains-plugin-development to Repair this JetBrains plug-in,
    but IDE builds and compatible Gradle/Kotlin versions are unknown.”
  - Route: `jetbrains-plugin-development`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $vscode-extension-development to handle a VS Code extension.”
  - Route: `vscode-extension-development`
  - Reason: The requested adjacent capability is outside
    `jetbrains-plugin-development`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Fix this IDE extension”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $jetbrains-plugin-development to build, repair, or
    review an IntelliJ Platform plug-in, then use
    $test-software-behavior
    for the related follow-up.”
  - Route: `jetbrains-plugin-development`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `maintain-agent-skills`

- **Direct**
  - Prompt: “Use $maintain-agent-skills to create, audit, or validate Agent
    Skills packages.”
  - Route: `maintain-agent-skills`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Audit this Agent Skill package and update its metadata and
    references.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $maintain-agent-skills to Audit these Agent Skills, but the
    package scope and requested outcome are absent.”
  - Route: `maintain-agent-skills`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $maintain-agents-md to handle an AGENTS.md file.”
  - Route: `maintain-agents-md`
  - Reason: The requested adjacent capability is outside
    `maintain-agent-skills`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Improve agent guidance”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $maintain-agent-skills to create, audit, or
    validate Agent Skills packages, then use
    $maintain-repository-docs
    for the related follow-up.”
  - Route: `maintain-agent-skills`, then `maintain-repository-docs`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `maintain-agents-md`

- **Direct**
  - Prompt: “Use $maintain-agents-md to create or audit scoped AGENTS.md
    instructions.”
  - Route: `maintain-agents-md`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Write AGENTS.md guidance for this repository from its existing
    scripts and CI.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $maintain-agents-md to Create AGENTS.md, but its intended
    directory scope is absent.”
  - Route: `maintain-agents-md`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $maintain-agent-skills to repair this SKILL.md package and its
    invocation metadata.”
  - Route: `maintain-agent-skills`
  - Reason: Skill-package maintenance does not edit repository instruction
    precedence.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Improve agent guidance”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $maintain-agents-md to create or audit scoped
    AGENTS.md instructions, then use $maintain-repository-docs
    for the related follow-up.”
  - Route: `maintain-agents-md`, then `maintain-repository-docs`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `maintain-changelog`

- **Direct**
  - Prompt: “Use $maintain-changelog to write, audit, or validate a changelog or
    SemVer decision.”
  - Route: `maintain-changelog`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Prepare release notes and decide the SemVer bump from these public
    API changes.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $maintain-changelog to Update the changelog, but the release
    facts and candidate version are unknown.”
  - Route: `maintain-changelog`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $manage-hosted-repositories to handle publish a hosted
    release.”
  - Route: `manage-hosted-repositories`
  - Reason: The requested adjacent capability is outside `maintain-changelog`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Prepare a release”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $maintain-changelog to write, audit, or validate a
    changelog or SemVer decision, then use $manage-git-state
    for the related follow-up.”
  - Route: `maintain-changelog`, then `manage-git-state`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `maintain-repository-docs`

- **Direct**
  - Prompt: “Use $maintain-repository-docs to write or audit repository
    documentation.”
  - Route: `maintain-repository-docs`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Update the README installation instructions from the actual package
    scripts.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $maintain-repository-docs to Update the README, but the
    intended document and executable evidence are not identified.”
  - Route: `maintain-repository-docs`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $maintain-changelog to handle a changelog.”
  - Route: `maintain-changelog`
  - Reason: The requested adjacent capability is outside
    `maintain-repository-docs`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Improve the documentation”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $maintain-repository-docs to write or audit
    repository documentation, then use
    $configure-repository-governance
    for the related follow-up.”
  - Route: `maintain-repository-docs`, then `configure-repository-governance`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `manage-git-state`

- **Direct**
  - Prompt: “Use $manage-git-state to make a scoped local Git state change.”
  - Route: `manage-git-state`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Commit only the staged documentation changes and preserve the
    remaining worktree edits.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $manage-git-state to Recover this Git state, but the desired
    ref or restoration point is unknown.”
  - Route: `manage-git-state`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $manage-hosted-repositories to handle a hosted pull request.”
  - Route: `manage-hosted-repositories`
  - Reason: The requested adjacent capability is outside `manage-git-state`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Clean up Git”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $manage-git-state to make a scoped local Git state
    change, then use $find-regression-commit
    for the related follow-up.”
  - Route: `manage-git-state`, then `find-regression-commit`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `manage-hosted-repositories`

- **Direct**
  - Prompt: “Use $manage-hosted-repositories to manage a GitHub or GitLab hosted
    resource.”
  - Route: `manage-hosted-repositories`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Create a GitHub issue with this body and labels.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $manage-hosted-repositories to Update this hosted resource, but
    the provider, repository, and resource identity are absent.”
  - Route: `manage-hosted-repositories`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $manage-git-state to handle a local commit.”
  - Route: `manage-git-state`
  - Reason: The requested adjacent capability is outside
    `manage-hosted-repositories`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Publish the change”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $manage-hosted-repositories to manage a GitHub or
    GitLab hosted resource, then use $maintain-changelog
    for the related follow-up.”
  - Route: `manage-hosted-repositories`, then `maintain-changelog`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `migrate-bun-toolchain`

- **Direct**
  - Prompt: “Use $migrate-bun-toolchain to adopt Bun or migrate an existing Bun
    tooling surface.”
  - Route: `migrate-bun-toolchain`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Upgrade this project's Bun runtime while preserving its existing
    Node-only scripts.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $migrate-bun-toolchain to Migrate Bun, but the current version,
    target, and affected tooling surfaces are unknown.”
  - Route: `migrate-bun-toolchain`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $optimize-bun-code to handle Bun performance profiling.”
  - Route: `optimize-bun-code`
  - Reason: The requested adjacent capability is outside
    `migrate-bun-toolchain`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Modernize JavaScript tooling”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $migrate-bun-toolchain to adopt Bun or migrate an
    existing Bun tooling surface, then use $test-software-behavior
    for the related follow-up.”
  - Route: `migrate-bun-toolchain`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `neovim-plugin-development`

- **Direct**
  - Prompt: “Use $neovim-plugin-development to build, repair, or review a Neovim
    Lua plug-in.”
  - Route: `neovim-plugin-development`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add a buffer-local Neovim command and clean up its augroup on
    teardown.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $neovim-plugin-development to Repair this Neovim plug-in, but
    its supported version and runtimepath layout are unknown.”
  - Route: `neovim-plugin-development`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $sublime-plugin-development to handle a Sublime Text package.”
  - Route: `sublime-plugin-development`
  - Reason: The requested adjacent capability is outside
    `neovim-plugin-development`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Fix this editor plug-in”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $neovim-plugin-development to build, repair, or
    review a Neovim Lua plug-in, then use $test-software-behavior
    for the related follow-up.”
  - Route: `neovim-plugin-development`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `operate-duckstation`

- **Direct**
  - Prompt: “Use $operate-duckstation to run or diagnose an isolated DuckStation
    PS1 fixture.”
  - Route: `operate-duckstation`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Launch this DuckStation PS1 fixture in an isolated data tree and
    capture its checkpoint.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $operate-duckstation to Operate DuckStation, but the build,
    game revision, and checkpoint are unknown.”
  - Route: `operate-duckstation`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $compile-duckstation-from-source to handle compiling
    DuckStation.”
  - Route: `compile-duckstation-from-source`
  - Reason: The requested adjacent capability is outside `operate-duckstation`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Debug this emulator game”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $operate-duckstation to run or diagnose an isolated
    DuckStation PS1 fixture, then use $test-software-behavior
    for the related follow-up.”
  - Route: `operate-duckstation`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `operate-pcsx2`

- **Direct**
  - Prompt: “Use $operate-pcsx2 to run or diagnose an isolated PCSX2 PS2
    fixture.”
  - Route: `operate-pcsx2`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Launch this PCSX2 PS2 fixture in an isolated data tree and capture
    its checkpoint.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $operate-pcsx2 to Operate PCSX2, but the build, game revision,
    and checkpoint are unknown.”
  - Route: `operate-pcsx2`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $compile-pcsx2-from-source to handle compiling PCSX2.”
  - Route: `compile-pcsx2-from-source`
  - Reason: The requested adjacent capability is outside `operate-pcsx2`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Debug this emulator game”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $operate-pcsx2 to run or diagnose an isolated PCSX2
    PS2 fixture, then use $test-software-behavior
    for the related follow-up.”
  - Route: `operate-pcsx2`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `optimize-bun-code`

- **Direct**
  - Prompt: “Use $optimize-bun-code to measure and optimize a Bun application's
    performance.”
  - Route: `optimize-bun-code`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Profile Bun RSS growth under this fixed workload and optimize the
    measured path.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $optimize-bun-code to Optimize this Bun program, but no
    workload or performance metric is supplied.”
  - Route: `optimize-bun-code`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $migrate-bun-toolchain to handle a Bun version migration.”
  - Route: `migrate-bun-toolchain`
  - Reason: The requested adjacent capability is outside `optimize-bun-code`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Make this JavaScript faster”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $optimize-bun-code to measure and optimize a Bun
    application's performance, then use $test-software-behavior
    for the related follow-up.”
  - Route: `optimize-bun-code`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `optimize-dotnet-code`

- **Direct**
  - Prompt: “Use $optimize-dotnet-code to measure and optimize a .NET
    application's performance.”
  - Route: `optimize-dotnet-code`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Profile this .NET service's p99 latency under the supplied
    workload.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $optimize-dotnet-code to Optimize this .NET program, but no
    workload, metric, target framework, or runtime is supplied.”
  - Route: `optimize-dotnet-code`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $optimize-rust-code to profile this Rust executable; the
    surrounding service uses .NET.”
  - Route: `optimize-rust-code`
  - Reason: The actual performance target is Rust, not the surrounding .NET
    service.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Make this application faster”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $optimize-dotnet-code to measure and optimize a
    .NET application's performance, then use $test-software-behavior
    for the related follow-up.”
  - Route: `optimize-dotnet-code`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `optimize-rust-code`

- **Direct**
  - Prompt: “Use $optimize-rust-code to measure and optimize Rust performance.”
  - Route: `optimize-rust-code`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Profile allocations in this Rust parser under its fixed benchmark
    workload.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $optimize-rust-code to Optimize this Rust program, but no
    workload, build profile, or target CPU is supplied.”
  - Route: `optimize-rust-code`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $optimize-dotnet-code to profile this C# service; leave its
    Rust sidecar unchanged.”
  - Route: `optimize-dotnet-code`
  - Reason: The actual performance target is .NET, not the adjacent Rust
    process.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Make this application faster”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $optimize-rust-code to measure and optimize Rust
    performance, then use $test-software-behavior
    for the related follow-up.”
  - Route: `optimize-rust-code`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `remove-legacy-compatibility`

- **Direct**
  - Prompt: “Use $remove-legacy-compatibility to remove confirmed obsolete
    compatibility surfaces.”
  - Route: `remove-legacy-compatibility`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Remove this obsolete alias after tracing all supported consumers.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $remove-legacy-compatibility to Remove legacy compatibility,
    but no replacement or retirement evidence is supplied.”
  - Route: `remove-legacy-compatibility`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $design-software-boundaries to handle an active API migration.”
  - Route: `design-software-boundaries`
  - Reason: The requested adjacent capability is outside
    `remove-legacy-compatibility`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Remove old code”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $remove-legacy-compatibility to remove confirmed
    obsolete compatibility surfaces, then use
    $test-software-behavior
    for the related follow-up.”
  - Route: `remove-legacy-compatibility`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `review-software-security`

- **Direct**
  - Prompt: “Use $review-software-security to threat-model or defensively review
    software security.”
  - Route: `review-software-security`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Review this authorization boundary for exploitable privilege
    escalation.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $review-software-security to Review this security concern, but
    the authorized repository, entrypoints, and deployed version are unknown.”
  - Route: `review-software-security`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $test-software-behavior to add regression coverage for this
    already fixed authorization defect.”
  - Route: `test-software-behavior`
  - Reason: The requested output is behavioral coverage, not a new security
    review or certification.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Is this safe”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $review-software-security to threat-model or
    defensively review software security, then use
    $test-software-behavior
    for the related follow-up.”
  - Route: `review-software-security`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `sublime-plugin-development`

- **Direct**
  - Prompt: “Use $sublime-plugin-development to build, repair, or review a
    Sublime Text package.”
  - Route: `sublime-plugin-development`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add a Sublime Text command that applies edits within command
    ownership.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $sublime-plugin-development to Repair this Sublime package, but
    supported builds and embedded Python versions are unknown.”
  - Route: `sublime-plugin-development`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $neovim-plugin-development to handle a Neovim plug-in.”
  - Route: `neovim-plugin-development`
  - Reason: The requested adjacent capability is outside
    `sublime-plugin-development`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Fix this editor plug-in”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $sublime-plugin-development to build, repair, or
    review a Sublime Text package, then use $test-software-behavior
    for the related follow-up.”
  - Route: `sublime-plugin-development`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `test-software-behavior`

- **Direct**
  - Prompt: “Use $test-software-behavior to design, add, or review behavioral or
    regression tests.”
  - Route: `test-software-behavior`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add a regression test that fails on this fixed serialization bug.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $test-software-behavior to Test this behavior, but its intended
    contract and observable failure are not supplied.”
  - Route: `test-software-behavior`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent — coordinator correction**
  - Prompt: “Use $develop-ci-pipelines to repair the GitHub Actions job that
    uploads existing test reports.”
  - Route: `develop-ci-pipelines`
  - Reason: Pipeline artifact handling is separate from designing application
    tests.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Increase coverage”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $test-software-behavior to design, add, or review
    behavioral or regression tests, then use
    $review-software-security
    for the related follow-up.”
  - Route: `test-software-behavior`, then `review-software-security`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `vscode-extension-development`

- **Direct**
  - Prompt: “Use $vscode-extension-development to build, repair, or review a VS
    Code extension.”
  - Route: `vscode-extension-development`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add a VS Code command that works in the browser host and honors
    Workspace Trust.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $vscode-extension-development to Repair this VS Code extension,
    but its engines.vscode range and target hosts are unknown.”
  - Route: `vscode-extension-development`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $editor-extension-design to handle an editor-host choice.”
  - Route: `editor-extension-design`
  - Reason: The requested adjacent capability is outside
    `vscode-extension-development`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Fix this editor plug-in”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $vscode-extension-development to build, repair, or
    review a VS Code extension, then use $test-software-behavior
    for the related follow-up.”
  - Route: `vscode-extension-development`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

### `zed-extension-development`

- **Direct**
  - Prompt: “Use $zed-extension-development to build, repair, or review a Zed
    extension.”
  - Route: `zed-extension-development`
  - Reason: exact named invocation and in scope.
- **Paraphrased**
  - Prompt: “Add a Zed language extension with matching grammar IDs and manifest
    paths.”
  - Route: none
  - Reason: in scope semantically, but named invocation is required.
- **Incomplete**
  - Prompt: “Use $zed-extension-development to Repair this Zed extension, but
    the requested host API version and extension.toml are unknown.”
  - Route: `zed-extension-development`
  - Reason: Named and in scope; execution details must be resolved first.
- **Adjacent**
  - Prompt: “Use $vscode-extension-development to handle a VS Code extension.”
  - Route: `vscode-extension-development`
  - Reason: The requested adjacent capability is outside
    `zed-extension-development`.
- **Negative**
  - Prompt: “Recommend a vegetarian dinner for four people.”
  - Route: none
  - Reason: Unrelated to this catalog capability.
- **Ambiguous**
  - Prompt: “Fix this editor plug-in”
  - Route: none
  - Reason: The goal does not identify this capability over its neighbors.
- **Combined**
  - Prompt: “Use
    $zed-extension-development to build, repair, or
    review a Zed extension, then use $test-software-behavior
    for the related follow-up.”
  - Route: `zed-extension-development`, then `test-software-behavior`
  - Reason: both are explicitly named; keep their distinct outputs and
    prerequisites.

## Integration findings and corrections

The initial reviewer report incorrectly treated any named skill as suitable for
the requested work. It routed .NET and Rust SDK migration requests to the Bun
migration skill, ordinary implementation to architecture design, custom-agent
personas to Agent Skills maintenance, compliance certification to repository
documentation, and routine test execution to pipeline development. Those claims
were rejected: explicit invocation can load a skill without making an unrelated
workflow applicable. No underlying metadata expansion is warranted.

Nine adjacent cases above were replaced with concrete neighboring capabilities
and are labeled coordinator corrections. The replaced emulator/governance,
architecture/formatting and generic-debugging cases were also too weak to test
meaningful adjacency. The remaining 201 cases retain the independent reviewer's
classifications. There are 210 current cases, not 210 independent successful
client activations. The inherited broad seven-category semantic audits remain
separate historical evidence.

No skill-description change was needed. The catalog reserves implicit matching
for the two planning skills; named invocation does not override scope or
authorize side effects. Bare positive paraphrases intentionally test the
manual-policy boundary rather than claiming the capability is absent.

## Validation limits

The reviewer read 30 frontmatter files and 30 metadata files before bodies. The
coordinator inspected the resulting routes and corrected the cases identified
above. Neither pass exercised a client loader or ran domain workflows. Actual
workflow evidence is recorded in the domain evaluations. Formatting and strict
Markdown checks passed after integration.
