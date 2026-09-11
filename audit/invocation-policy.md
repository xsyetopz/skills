# Invocation-policy decision

Decision: 2026-09-12, following the user's explicit delegation to determine
which skills must never activate implicitly. This supersedes the earlier
assumption that only a named per-skill user request could change the policy.

## Explicit-only workflows

Keep `policy.allow_implicit_invocation: false` for:

- `interrogate-plan`: this changes the interaction into a sustained questioning
  workflow. Mentioning a plan, requirement, assumption, or risk in normal
  engineering work should not opt the user into that mode.
- `format-github-markdown`: this selects a particular bundled formatting policy
  and can introduce tooling. Mentioning Markdown or editing a README should not
  invoke that policy instead of the repository's existing conventions.

Both descriptions state the named-invocation requirement. Their bodies now
repeat it so an agent reading the package directly receives the same boundary.
The YAML setting remains false; no temporary true state was introduced.

## Normal discovery for task-specific capabilities

Retain normal discovery for the remaining skills. This decision does not mean
“activate on a keyword.” Select them only when their capability matches the
requested outcome:

- Editor implementation skills require work on the named editor's extension
  contract; mentioning an editor while building an unrelated application does
  not qualify. Cross-editor choice/port design has its own distinct outcome.
- Git state, hosted issues, PRs, settings, releases, and pipeline skills require
  the corresponding operation. A commit hash, issue link, or CI log appearing as
  context is not a request to modify that surface.
- Architecture, security, testing, performance, compatibility removal, and Bun
  migration require their named design/review/investigation/change outcome. An
  ordinary implementation task does not become a separate audit because it
  mentions tests, security, speed, dependencies, or legacy code.
- Repository documents, governance, AGENTS.md, changelogs, and Agent Skills
  maintenance require work on those artifacts, not simply their mention.
- Emulator launch, guest debugging, patches, textures, and builds require the
  corresponding emulator-specific operation, not merely discussion of a game.

These groups have useful discoverable safety and technical guidance for clear
natural-language requests. Making all of them explicit-only would suppress that
support even when the task unmistakably matches. Dangerous side effects still
require authorization; removing a skill from discovery is not a substitute for
an authorization check.

The catalog evaluations contain direct and neighboring/negative cases rather
than just keyword lists. Their observations do not justify blanket disabling.
Future demonstrated over-activation should first narrow an ambiguous boundary;
use explicit-only policy when the workflow itself is intentionally opt-in.
Revisit this decision if actual host activation disagrees with these boundaries.

## Enforcement and evidence limits

The [Codex skills guide](https://learn.chatgpt.com/docs/build-skills) defines
the YAML field as a Codex invocation control. It is not part of the portable
[Agent Skills specification](https://agentskills.io/specification). Therefore
this repository cannot guarantee that every agent implementation enforces it.
The explicit description/body contract addresses agents that read instructions;
other clients need their own supported loading/invocation controls.

The two false values and all remaining default policies were parsed and checked
in the current 38-skill worktree. This is configuration and contract evidence,
not a universal runtime enforcement test. The `maintain-agent-skills` guidance
now explains delegated policy decisions, keyword-versus-task matching, and
client-specific enforcement without inventing a portable policy field.
