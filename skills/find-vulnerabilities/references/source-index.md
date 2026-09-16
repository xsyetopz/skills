# Source index and freshness rules

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

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
