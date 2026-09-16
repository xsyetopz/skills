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
| [Microsoft Azure architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/) | Use as an option catalogue and tradeoff guide, not a mandatory cloud design. |
| [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/) | Use when AWS workload review is relevant; preserve other-platform controls. |
| [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) | Use for secure-development lifecycle controls when applicable. |
| [aws.amazon.com: making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: extension host](https://code.visualstudio.com/api/advanced-topics/extension-host) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cognitect.com: documenting architecture decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [developer.android.com: ui layer](https://developer.android.com/topic/architecture/ui-layer) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [doc.rust-lang.org: features.html](https://doc.rust-lang.org/cargo/reference/features.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [doc.rust-lang.org: visibility and privacy.html](https://doc.rust-lang.org/reference/visibility-and-privacy.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.aws.amazon.com: transactional outbox.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.oracle.com: jls 7.html](https://docs.oracle.com/javase/specs/jls/se25/html/jls-7.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: microsoft/debug-adapter-protocol — debugAdapterProtocol.json](https://github.com/microsoft/debug-adapter-protocol/blob/main/debugAdapterProtocol.json) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: openapi-ts/openapi-typescript — ts.ts](https://github.com/openapi-ts/openapi-typescript/blob/main/packages/openapi-typescript/src/lib/ts.ts) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [go.dev: layout](https://go.dev/doc/modules/layout) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [google.github.io: looking for.html](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: pde overview.htm](https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/intro/pde_overview.htm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [isocpp.github.io: CppCoreGuidelines#S source](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-source) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [json-schema.org: 2020 12](https://json-schema.org/draft/2020-12) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: mvvm](https://learn.microsoft.com/en-us/dotnet/architecture/maui/mvvm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: file](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/file) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: namespaces](https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/namespaces) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: source generation](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/source-generation) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [microsoft.github.io: overview](https://microsoft.github.io/debug-adapter-protocol/overview) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [microsoft.github.io: specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [microsoft.github.io: #baseProtocol](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#baseProtocol) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [microsoft.github.io: #textDocument synchronization](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_synchronization) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [microsoft.github.io: #workspaceEdit](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspaceEdit) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [neovim.io: api](https://neovim.io/doc/user/api/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [opentelemetry.io: handling sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [opentelemetry.io: http spans](https://opentelemetry.io/docs/specs/semconv/http/http-spans/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [packaging.python.org: src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [peps.python.org: pep 0008](https://peps.python.org/pep-0008/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pkg.go.dev: cgo](https://pkg.go.dev/cmd/cgo) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pkg.go.dev: sql](https://pkg.go.dev/database/sql) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pkg.go.dev: sqlite](https://pkg.go.dev/modernc.org/sqlite) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: welcome.html](https://plugins.jetbrains.com/docs/intellij/welcome.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [react.dev: managing state](https://react.dev/learn/managing-state) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [registry.npmjs.org: 7.13.0](https://registry.npmjs.org/openapi-typescript/7.13.0) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [slsa.dev: v1.0](https://slsa.dev/spec/v1.0/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [spec.openapis.org: latest.html](https://spec.openapis.org/oas/latest.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [sre.google: error budget policy](https://sre.google/workbook/error-budget-policy/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [sre.google: implementing slos](https://sre.google/workbook/implementing-slos/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.enterpriseintegrationpatterns.com: www.enterpriseintegrationpatterns.com](https://www.enterpriseintegrationpatterns.com/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.iso.org: 78176.html](https://www.iso.org/standard/78176.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.melconway.com: Committees Paper.html](https://www.melconway.com/Home/Committees_Paper.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.open-std.org: n3096.pdf](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3096.pdf) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.rfc-editor.org: rfc9110.html](https://www.rfc-editor.org/rfc/rfc9110.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.rfc-editor.org: rfc9110.html#section 13](https://www.rfc-editor.org/rfc/rfc9110.html#section-13) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.rfc-editor.org: rfc9111.html](https://www.rfc-editor.org/rfc/rfc9111.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.rfc-editor.org: rfc9457.html](https://www.rfc-editor.org/rfc/rfc9457.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sei.cmu.edu: architecture tradeoff analysis method collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: api reference.html](https://www.sublimetext.com/docs/api_reference.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.typescriptlang.org: reference.html](https://www.typescriptlang.org/docs/handbook/modules/reference.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: developing extensions](https://zed.dev/docs/extensions/developing-extensions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
