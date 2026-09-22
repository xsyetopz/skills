# Standards, APIs, and authorities for Software Security Review

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
| [OWASP ASVS 5.0](https://github.com/OWASP/ASVS/tree/v5.0.0) | Use as a verification catalogue when applicable, not automatic certification. |
| [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) | Secure software development controls. |
| [SLSA specification](https://slsa.dev/spec/v1.2/) | Supply-chain provenance and build integrity concepts. |
| [cheatsheetseries.owasp.org: Authorization Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: Cryptographic Storage Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: Deserialization Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: File Upload Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: LLM Prompt Injection Prevention Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: Logging Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: SQL Injection Prevention Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: Server Side Request Forgery Prevention Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cheatsheetseries.owasp.org: Threat Modeling Cheat Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [clang.llvm.org: AddressSanitizer.html](https://clang.llvm.org/docs/AddressSanitizer.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [clang.llvm.org: ThreadSanitizer.html](https://clang.llvm.org/docs/ThreadSanitizer.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [csrc.nist.gov: publications](https://csrc.nist.gov/projects/ssdf/publications) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cwe.mitre.org: 367.html](https://cwe.mitre.org/data/definitions/367.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cyclonedx.org: overview](https://cyclonedx.org/specification/overview/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [owasp.org: www project web security testing guide](https://owasp.org/www-project-web-security-testing-guide/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [spdx.dev: specifications](https://spdx.dev/use/specifications/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.rfc-editor.org: rfc8725](https://www.rfc-editor.org/rfc/rfc8725) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.rfc-editor.org: rfc9700](https://www.rfc-editor.org/rfc/rfc9700) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.usenix.org: spracklen](https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Agent behavior and skill-authoring authorities

These sources govern how an agent loads and applies this skill while it works on
security finding. They supplement the domain authorities in the earlier source
table for Find Vulnerabilities.

| Source | Rule applied in this skill |
| --- | --- |
| [OpenAI GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) | State intent, constraints, autonomy, tools, and success evidence once; compare model and reasoning settings with task evaluations instead of assuming more reasoning is better. |
| [OpenAI GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model) | Keep instructions lean, resolve conflicts, make follow-through and approval boundaries explicit, and test behavior on the target model. |
| [OpenAI Codex prompting](https://developers.openai.com/codex/prompting) | Name relevant files, reproduction details, constraints, and verification for repository work. |
| [OpenAI Agent Skills](https://developers.openai.com/codex/skills) | Keep the capability focused and route from `SKILL.md` to task-relevant resources. |
| [Anthropic Agent Skills overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) | Treat a skill as a discoverable directory with progressive resource loading. |
| [Anthropic authoring practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Match instruction detail to task fragility and evaluate on intended models. |
| [Anthropic skill engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | Inspect actual trajectories and use deterministic scripts where generated mechanics create avoidable error. |
| [Agent Skills home](https://agentskills.io/home) and [specification](https://agentskills.io/specification) | Preserve portable frontmatter and progressive disclosure; keep client metadata separate. |
| [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices) | Derive procedures from real tasks, state defaults, include gotchas, and close the plan-validate-execute loop. |
| [Description optimization](https://agentskills.io/skill-creation/optimizing-descriptions) | Test positive, near-miss, and competing-skill activation on the target client. |
| [Skill evaluation](https://agentskills.io/skill-creation/evaluating-skills) | Use realistic `evals/evals.json` cases, clean contexts, paired baselines, objective assertions, and artifact review. |
| [Using scripts](https://agentskills.io/skill-creation/using-scripts) | Prefer direct native commands; add a script only for repeated deterministic work and test its error paths. |
| [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) | Reserve normative keywords for requirements whose violation causes a material safety, correctness, or interoperability failure. |
| [ASD-STE100](https://www.asd-ste100.org/) | Use controlled technical English principles to reduce ambiguity; do not claim formal conformance without a licensed conformance review. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
