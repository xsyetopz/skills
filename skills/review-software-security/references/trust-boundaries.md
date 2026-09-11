# Review the boundary that can fail

Select checks from reachable inputs and operations. This is a review guide, not
a requirement to add every listed mechanism to every application.

## Identity and authorization

Authentication establishes identity; authorization governs an action on a
resource. Verify tenant/object ownership and action permissions at the server or
other authoritative boundary, including batch and background paths. Permissions
should not depend solely on client state or guess-resistant identifiers.
Exercise authorized, anonymous, wrong-role, and cross-owner cases where those
actors exist. Use the established [authorization model][authorization], not a
parallel policy engine invented during review.

When OAuth is present, use [RFC 9700][oauth] and the provider's supported flows.
Public authorization-code clients must use PKCE; confidential clients are also
recommended to use it. Bind login transactions and redirects through the
maintained client implementation. Do not propose resource-owner-password grants
or implicit token delivery as a new default. OAuth access tokens are not
interchangeable with OIDC ID tokens.

For JWTs, a library's successful decode is not validation. Check algorithm
policy, key/issuer trust, audience, time restrictions, and token-type separation
against the actual protocol. Do not let untrusted token headers select arbitrary
remote keys. [JWT best current practices][jwt] supplies the security
constraints; verify the chosen library's validation API rather than hand-rolling
signatures.

For cookie-authenticated browser writes, investigate framework CSRF protection,
cookie scope, and origin handling. CORS is not authorization. For password/key
handling, use supported identity services or maintained cryptographic libraries
and current platform guidance; do not construct custom encryption or password
hashing schemes. Separate key storage, rotation, and compromise response from
the encryption algorithm. [OWASP cryptographic storage][crypto].

## Untrusted input and executable contexts

Trace values into SQL, shells, templates, paths, and deserializers. Bind SQL
data parameters rather than concatenating them; dynamic identifiers require a
constrained mapping because value parameters cannot stand for SQL syntax. Test
with real driver execution, not a mock that merely records a query string.
[OWASP SQL injection prevention][sql].

Use subprocess argument APIs instead of a shell when a shell is unnecessary.
That does not neutralize option injection: distinguish options from operand data
using the invoked program's documented interface. For HTML, use the framework's
context-appropriate escaping; an encoding safe in HTML text is not automatically
safe in a URL or script. Check the actual sink, not a generic “sanitized” flag.

Prefer data-only standard formats and maintained parsers. Do not deserialize
attacker-controlled runtime objects such as Python pickle. Configure entity,
reference, depth, and size behavior where the parser supports it and the input
boundary needs it. A filename extension does not establish trustworthy contents.
[OWASP deserialization guidance][deserialize].

## Files, network, and resource limits

For uploads/archives, verify permitted types, storage outside executable/public
locations where appropriate, service-owned destination names, access control,
and realistic size limits. Account for expanded size, entry count, traversal,
links, and overwrite behavior if archives are extracted. Use existing extraction
facilities only after checking their documented policy; do not build an archive
parser. [OWASP file upload guidance][uploads].

A path-prefix string check is not containment. Resolve path semantics using the
target platform and consider symlink replacement if an attacker can mutate the
directory. Checking a path and later reopening it creates a potential race;
prefer an operation on the validated handle or an appropriate directory-relative
API when the platform supports it. Demonstrate attacker control before demanding
race defenses. [CWE-367][toctou].

For server-side fetching, verify destination policy at connection time, schemes,
redirects, DNS results, proxy behavior, and outbound network controls. Checking
only the initial URL or one resolved address is insufficient when a later
redirect or resolution changes the destination. Do not invent a URL/IP parser.
Prefer a limited allowlist when the feature has known destinations; unrestricted
fetchers need a broader egress design. [OWASP SSRF prevention][ssrf].

Apply resource limits at reachable costly operations: request bodies,
decompression, query fan-out, pagination, regex processing, subprocesses, and
queued work. Derive limits from the service contract and measurements; arbitrary
universal caps can break legitimate workloads. Rate limiting does not repair
missing authorization.

## Native memory, concurrency, and privacy

At unsafe/FFI boundaries, identify ownership, allocation/free pairing, lengths,
alignment, lifetime, aliasing, and thread requirements. Validate using matching
toolchain instrumentation and representative execution. [AddressSanitizer][asan]
detects classes of memory errors; [ThreadSanitizer][tsan] targets data races.
Neither proves all executions safe. Check platform support and instrumentation
coverage before interpreting a clean run.

Review state changes under concurrency: authorization followed by a stale
update, double use of a one-time token, or a check followed by a separate write
may require an atomic database condition or transaction. Adding a process-local
lock is not cross-process correctness. Reproduce with controlled interleavings,
not only load.

Check logs, errors, telemetry, caches, and exports for credentials, tokens,
personal data, or cross-tenant leakage. Retain enough structured context for
diagnosis without raw secrets. Treat log fields as untrusted data and test
failure behavior when logging fails. [OWASP logging guidance][logging].

[authorization]:
  https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
[oauth]: https://www.rfc-editor.org/rfc/rfc9700
[jwt]: https://www.rfc-editor.org/rfc/rfc8725
[crypto]:
  https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
[sql]:
  https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
[deserialize]:
  https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
[uploads]:
  https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
[toctou]: https://cwe.mitre.org/data/definitions/367.html
[ssrf]:
  https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[tsan]: https://clang.llvm.org/docs/ThreadSanitizer.html
[logging]:
  https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
