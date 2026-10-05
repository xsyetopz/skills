# XsyeTopz Skills

My reusable skills for AI coding agents.

## Skills

- `review-scientific-paper`: Evidence-checked answers from research papers.
- `audit-agent-sessions`: Find wasted turns and tokens in Claude Code transcripts.
- `decompile-to-matching-c-cpp`: Match decompiled functions byte for byte.
- `write-ci-workflow`: Write and fix CI workflows that fail correctly.
- `write-agent-hooks`: Write and debug Claude Code and Codex hooks.
- `write-agent-stop-condition`: Keep the agent working until a check passes.
- `write-agent-skill`: Write, trim, and evaluate Agent Skills.
- `debug-game-in-emulator`: Debug games in PCSX2, DuckStation, Dolphin, RPCS3, and more.
- `write-emulator-patches`: Write and fix emulator patches, cheats, and their settings.
- `commit-and-rewrite-git`: Commit, stage, rewrite, recover, and bisect git history.
- `design-cli-interface`: Design, change, and rename CLI commands safely.
- `build-editor-extension`: Build, test, and package editor extensions.
- `format-github-markdown`: Fix anchors, Contents lists, and markdownlint errors.
- `write-architecture-md`: ARCHITECTURE.md codemaps checked against the code.
- `write-project-readme`: README, CONTRIBUTING, and API docs whose commands run.
- `audit-repo-secrets-and-ci`: Find leaked secrets, unsafe CI workflows, and proven code bugs.
- `test-game-exploits`: Find and fix cheats in your own game before players do.
- `refactor-code-smells`: Refactor smells and dead shims without behavior change.
- `apply-architecture-patterns`: Fit new code to the codebase's architecture.
- `fix-diagnostics-without-suppressing`: Fix warnings and deprecations at the cause.
- `bump-semver`: Pick the next SemVer version and drop due shims.
- `update-changelog`: Write user-facing CHANGELOG entries and sections.
- `migrate-js-to-bun`: Move npm, Yarn, pnpm, and Jest to Bun.
- `optimize-runtime-performance`: Profile and speed up hot code paths safely.
- `optimize-tsc-builds`: Speed up tsc, tsgo, and type checking.
- `interview-to-openspec`: Interview for decisions, then write an OpenSpec change.
- `recompile-console-binary`: Recompile console games into native C or C++.
- `reverse-engineer-binary`: Reverse-engineer binaries and firmware.
- `triage-github-prs-and-issues`: GitHub pull requests, issues, reviews, and labels with gh.
- `write-agents-md`: Write and audit AGENTS.md and CLAUDE.md for Claude Code and Codex.
- `write-behavior-tests`: Behavior tests that fail on real faults.
- `write-justfile`: Write just recipes that wrap project commands.

## Install

Use the [Vercel Skills CLI](https://skills.sh/docs/cli) with Bun to choose skills interactively:

```shell
bunx skills add xsyetopz/skills
```

Install every skill for every detected agent:

```shell
bunx skills add xsyetopz/skills --all
```

To install globally, add `--global`. To install one skill, use `--skill <name>`.

Update installed skills later with:

```shell
bunx skills update
```
