---
name: find-vulnerabilities
description: >-
  Finds exploitable vulnerabilities in code, configuration, and dependencies
  (injection, XSS, path traversal, SSRF, authorization, secrets, weak crypto)
  and proves each with a local test. Use for security reviews and audits. Not
  for probing live systems.
---

# Find Vulnerabilities

Find vulnerabilities an attacker can reach, and prove each one without
touching systems the user does not own. Map trust boundaries, trace
input to a sensitive sink, confirm the exploit condition with a local
test against a synthetic target, and report the finding with a CWE,
evidence class, severity vector, fix, and the test that proves the fix.

## Workflow

1. Write the scope: revision, components, allowed methods, exclusions
   ([scope](references/review-method.md#scope-and-rules-of-engagement)).
   Live hosts, real credentials, and production data stay out.
1. Build the trust-boundary map
   ([map](references/review-method.md#trust-boundary-map)).
1. Run the cheap scanners on the checkout and keep their output as
   leads, not findings:
   - `gitleaks dir --redact .` and `gitleaks git --redact .`, or
     `python3 scripts/scan_secrets.py .` when gitleaks is missing
   - the ecosystem audit for each lockfile (`cargo audit`,
     `bun audit`, `pip-audit`, `osv-scanner scan -r .`)
   - a local Semgrep taint rule with `--metrics=off`
1. For each lead and each boundary, trace source to sink with file:line
   per hop ([trace](references/review-method.md#source-to-sink-trace)).
   Match the sink to a card in the table below.
1. Confirm with a local exploit-condition test: vulnerable code shows
   the condition, fixed code blocks it, a legitimate input still works
   ([test](references/review-method.md#local-exploit-condition-test)).
   If you cannot build one, mark the finding a hypothesis.
1. Write each finding in the
   [finding format](references/review-method.md#finding-format), pick
   the CWE ([selection](references/review-method.md#cwe-selection)), and
   add a CVSS vector when the consumer uses CVSS
   ([v3.1](references/review-method.md#cvss-v31-base-vector),
   [v4.0](references/review-method.md#cvss-v40-base-vector)).
1. Run `python3 scripts/check_findings.py REVIEW.md` and
   `python3 scripts/scan_secrets.py REVIEW.md`; both must exit 0.

## Route the sink to a card

| Seen in code | Card |
| --- | --- |
| SQL built with `+`, f-string, `%`, `.format` | [SQL value parameters](references/injection.md#sql-value-parameters) |
| Column, table, or sort order from input | [SQL identifier allowlist](references/injection.md#sql-identifier-allowlist) |
| `shell=True`, `os.system`, `os.popen` | [Argument vector](references/injection.md#argument-vector-instead-of-a-shell) |
| argv operand from input to a CLI with options | [End-of-options marker](references/injection.md#end-of-options-marker) |
| Input between HTML tags | [HTML text escaping](references/injection.md#html-text-escaping) |
| Input in a quoted attribute | [Quoted attribute escaping](references/injection.md#quoted-attribute-escaping) |
| Input in `href` or `src` | [URL scheme allowlist](references/injection.md#url-scheme-allowlist-for-links) |
| Template environment, `\|safe`, `Markup` | [Template autoescape](references/injection.md#template-autoescape) |
| `from_string` or `render_template_string` on input | [Template data](references/injection.md#user-text-as-template-data-not-template-source) |
| File name or path from input joined to a dir | [Path containment](references/files-and-parsers.md#resolved-path-containment) |
| `tarfile` `extractall` | [Tar data filter](references/files-and-parsers.md#tar-extraction-data-filter) |
| `exists`, `access`, `is_symlink`, then open | [No-follow open](references/files-and-parsers.md#no-follow-open-then-check-the-descriptor), [exclusive create](references/files-and-parsers.md#exclusive-create) |
| `pickle.loads` on outside bytes | [JSON instead of pickle](references/files-and-parsers.md#json-instead-of-pickle), [restricted unpickler](references/files-and-parsers.md#restricted-unpickler) |
| `yaml.load` with `UnsafeLoader` or `Loader` | [YAML safe loader](references/files-and-parsers.md#yaml-safe-loader) |
| XML from outside (Python) | [SAX entities](references/files-and-parsers.md#sax-external-entities-left-off), [reject DOCTYPE](references/files-and-parsers.md#reject-doctype-in-stdlib-expat), [Expat limit](references/files-and-parsers.md#expat-amplification-limit), [defusedxml](references/files-and-parsers.md#defusedxml) |
| `DocumentBuilderFactory` and other Java XML factories | [disallow-doctype-decl](references/files-and-parsers.md#java-disallow-doctype-decl) |
| Server fetches a URL from input | [Allowlist and address check](references/web-and-access.md#host-allowlist-and-resolved-address-check), [redirect hops](references/web-and-access.md#re-check-every-redirect-hop), [checked address](references/web-and-access.md#connect-to-the-checked-address), [pinned HTTPS](references/web-and-access.md#pinned-https-with-hostname-verification) |
| Handler loads a record by client-supplied ID | [Object-level authorization](references/web-and-access.md#object-level-authorization) |
| Privileged action guarded only by login | [Function-level authorization](references/web-and-access.md#function-level-authorization) |
| JWT decode, OAuth callback | [Token validation](references/web-and-access.md#token-validation-at-the-boundary) |
| `random` for tokens, IDs, salts | [secrets module](references/crypto-and-secrets.md#secrets-module-for-tokens) |
| Fast or unsalted password hash | [scrypt](references/crypto-and-secrets.md#scrypt-password-hashing), [Argon2id](references/crypto-and-secrets.md#argon2id-password-hashing) |
| `==` on MACs, signatures, tokens | [Constant-time comparison](references/crypto-and-secrets.md#constant-time-digest-comparison) |
| Credentials in code or history | [gitleaks](references/crypto-and-secrets.md#gitleaks-secret-scan), [regex fallback](references/crypto-and-secrets.md#regex-fallback-secret-scan), [trufflehog](references/crypto-and-secrets.md#trufflehog-without-verification) |
| Headers, bodies, tokens written to logs | [Log redaction](references/crypto-and-secrets.md#log-redaction) |
| Audit tool advisory match | [Reachability triage](references/dependencies.md#advisory-triage-by-reachability), then the tool card |
| New dependency in the diff | [Package identity](references/dependencies.md#package-identity-before-install) |
| CI, signing, release credentials | [Provenance and SBOM](references/dependencies.md#provenance-and-sbom) |
| Model output reaches a tool | [Agent tool boundary](references/review-method.md#agent-tool-boundary) |
| Same source/sink shape in many handlers | [Semgrep taint rule](references/review-method.md#semgrep-taint-rule) |

## Rules

- Stay inside the written scope. Never send requests to hosts the user
  does not own, never try a credential you find, and run trufflehog only
  with `--no-verification`.
- A dangerous API name, scanner hit, or advisory match is a lead. It
  becomes a confirmed finding only with a traced path and a test or a
  complete argument; otherwise mark it a design risk or hypothesis
  ([evidence classes](references/review-method.md#evidence-classes)).
- Build proofs against synthetic targets: in-memory databases, temp
  directories, 127.0.0.1 servers, marker files, recorder functions.
  Never weaken authentication or authorization to make a proof work.
- Pick the CWE for the mistake, not the impact; avoid entries MITRE
  marks Discouraged (CWE-20, CWE-200, CWE-284) unless no lower entry
  fits.
- Record CVSS vectors and compute scores with the FIRST calculator;
  never type a score from a label. v4.0 metric order is mandatory.
- Keep reports free of live payloads, real secrets, and extracted
  data; see
  [reporting](references/review-method.md#reporting-without-weaponized-detail).
- A fix is done when the same test flips from exploit condition to
  blocked and a legitimate input still passes.

## Bundled tools

- `scripts/check_findings.py REVIEW.md [--json]`: reports findings that
  lack a required field, a CWE ID, a path:line location, a valid status,
  a `->` trace, or a valid CVSS v3.1 or v4.0 vector; exit 1 if any.
- `scripts/scan_secrets.py PATH... [--json]`: stdlib secret scan with
  redacted previews; exit 1 on any match.
- `assets/examples/`: vulnerable and fixed pairs with tests (`python/`,
  `java/`, `semgrep/`, `thirdparty/`), a worked `review.md`, and
  `verify.sh` (`local` needs no network; `network` runs the uv-based
  examples and dependency audits).

## References

- [Review method](references/review-method.md): scope, boundary map,
  tracing, Semgrep, evidence classes, local tests, finding format, CWE,
  CVSS v3.1 and v4.0, reporting, agent tool boundary.
- [Injection](references/injection.md): SQL, shell, argument, HTML
  contexts, templates.
- [Files and parsers](references/files-and-parsers.md): paths, tar,
  check-then-use races, pickle, YAML, XML in Python and Java.
- [Web and access](references/web-and-access.md): SSRF checks and
  pinning, object and function authorization, token validation.
- [Crypto and secrets](references/crypto-and-secrets.md): tokens,
  password hashing, digest comparison, secret scanners, log redaction.
- [Dependencies](references/dependencies.md): advisory triage, cargo
  audit, bun audit, pip-audit, osv-scanner, package identity,
  provenance.

## Completion evidence

The report states the scope and trust-boundary map; lists findings in
the finding format, each with evidence class, CWE, trace, the local test
or command and its result, remediation, and verification; lists "not
findings" with reasons; names every scanner run with its version and
exit status and every check skipped or unavailable; and includes the
`check_findings.py` summary line.
