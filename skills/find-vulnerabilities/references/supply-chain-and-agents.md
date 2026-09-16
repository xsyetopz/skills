# Review software dependencies and coding-agent permissions

## Verify dependency identity before installation

Discover the existing package manager, lockfile, registry configuration,
dependency policy, and target versions. Prefer a suitable
standard-library/platform facility or an already approved dependency. Before
adding a package, verify the exact name and registry against official project
documentation and source ownership. A package that exists is not necessarily the
project the agent intended; inspect publisher, repository, release history,
license, install hooks, and relevant advisories.

The peer-reviewed [USENIX Security 2025 package-hallucination study][packages]
observed nonexistent package recommendations across the models it evaluated.
This supports verifying identity rather than installing guessed names. Its
measured rates are not a forecast for every current model or ecosystem.
Existence checks alone cannot protect against a maliciously registered guessed
name.

Use the ecosystem's current advisory/audit tools on the resolved dependency
graph. Separate an advisory match from a confirmed reachable vulnerability;
inspect the affected version range and configuration. Lack of known advisories
is not proof of safety. Choose a supported patched version and test
compatibility instead of blindly upgrading everything or silencing the advisory.

## Review release authority

Trace source revision to builder, artifact digest, signer identity, publication,
and consumer verification. A checksum downloaded beside a compromised artifact
does not independently authenticate it. Pinning controls resolution; it does not
prove a dependency is benign. Least-privilege build/release credentials and
separation of untrusted pull-request code from release authority matter.

[SLSA 1.2][slsa] defines separate source/build tracks and their verification
expectations. Select the threat and applicable track rather than claiming a SLSA
level from “has CI.” Verify provenance against the intended source and trusted
builder, not merely the presence of a signed document. Provenance describes
origin; it is not a vulnerability-free certificate.

When a consumer requires an SBOM, use its accepted [SPDX][spdx] or
[CycloneDX][cyclonedx] version and an existing generator for the resolved
artifact. Do not invent a dependency manifest or confuse an SBOM with
provenance. Review completeness of native, vendored, optional, and build-time
components relevant to that artifact. Validate the required format with its
official tooling before publication.

## Agent-integrated features

In an agent application, retrieved documents, repository comments, issue text,
web content, and tool output can contain adversarial instructions. Keep those
inputs outside the authority that decides tool permissions and privileged
actions. Model output is also untrusted input to an executor. A prompt saying
“be safe” does not enforce access control. Apply allowlisted capabilities,
least-privilege credentials, bounded execution, and independent authorization at
the tool boundary. [OWASP prompt injection guidance][injection].

Test the composed workflow: a seemingly harmless read can return content that
requests a later secret-bearing network write. Use synthetic secrets and a local
recording tool to verify that the write is refused. Do not prove exfiltration by
sending real credentials. User consent to read data is not consent to follow its
embedded instructions or publish its contents.

For review reports, quote only the minimal adversarial text needed to explain
the failure. Never copy an embedded command into privileged execution merely to
understand it. Do not create custom signing, sandboxing, or prompt-filter
protocols when the host already supplies enforceable mechanisms.

[packages]:
https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen
[slsa]: https://slsa.dev/spec/v1.2/
[spdx]: https://spdx.dev/use/specifications/
[cyclonedx]: https://cyclonedx.org/specification/overview/
[injection]:
https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
