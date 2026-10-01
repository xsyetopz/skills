# Review method

## Contents

- [Evidence classes](#evidence-classes)
- [Local exploit-condition test](#local-exploit-condition-test)
- [Finding format](#finding-format)
- [CWE and CVSS](#cwe-and-cvss)
- [Reporting](#reporting)
- [Agent tool boundary](#agent-tool-boundary)

## Evidence classes

Each item is exactly one of:

- `confirmed`: traced end to end and demonstrated by a test, or fully argued under stated
  preconditions.
- `design risk`: a required control is missing from the design; no exploit path shown.
- `hypothesis`: evidence missing or contradictory. Name the observation that would settle it.

Never promote a hypothesis because the sink looks dangerous or a tool rated it critical. A confirmed
finding's Evidence names a runnable test or command and its observed result.

## Local exploit-condition test

Build the smallest test against a synthetic target: in-memory database, temp directory, 127.0.0.1
server, marker file, or recorder function.

1. Vulnerable code shows the condition (for example the marker file appears, or tenant A's record
   reaches tenant B).
1. Fixed code blocks it with the same input.
1. A legitimate input still passes through the fixed code.

If the target needs the real system, stop and mark a hypothesis.

## Finding format

`### F<n>: <title>` followed by these bullets (continuation lines indented two spaces).
`scripts/check_findings.py` enforces them.

```markdown
### F2: Invoice readable across tenants by ID

- CWE: CWE-639 Authorization Bypass Through User-Controlled Key
- Location: web.py:154 `get_invoice`
- Status: confirmed
- Preconditions: authenticated member of any tenant who guesses an ID
- Trace: path param `invoice_id` -> get_invoice(user, id) ->
  store[id] -> response
- Impact: reads another tenant's invoice totals
- Evidence: `test_other_tenant_reads_invoice_by_id` returns tenant a's
  invoice to a tenant b user
- Severity: CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N
- Remediation: filter by the caller's tenant; answer like a missing record
- Verification: `test_ownership_check_hides_other_tenant` raises
  NotFound; the owner still reads the invoice
```

If the repository has its own advisory template, fill that with the same facts. List hardening notes
with no attacker path separately. List "not findings" with the reason each was dismissed.

## CWE and CVSS

- Choose the CWE for the root mistake (for example CWE-89 for SQL built from input, CWE-22 for path
  traversal, CWE-502 for unsafe deserialization, CWE-918 for SSRF, CWE-639 for missing object-level
  check). Look up IDs in the [CWE API][cwe-api]; do not guess numbers. [CWE-20][cwe-20],
  [CWE-200][cwe-200], and [CWE-284][cwe-284] are Discouraged.
- Record the vector and score it in the FIRST calculator ([v3.1][calc31], [v4.0][calc40]); specs:
  [v3.1][cvss31], [v4.0][cvss40]. v4.0 vectors start `CVSS:4.0/` and list AV, AC, AT, PR, UI, VC,
  VI, VA, SC, SI, SA in that order. v3.1 vectors list AV, AC, PR, UI, S, C, I, A. Omit severity if
  the consumer does not use CVSS.

## Reporting

Keep live payloads, real secrets, and extracted data out of reports. Describe the payload class and
show the synthetic proof. Redact any credential to a prefix and its location. Run gitleaks over the
report before sharing it.

## Agent tool boundary

In an app where a model calls tools, retrieved content (documents, web pages, issue text, tool
output) and model output are untrusted input ([CWE-1427][cwe-1427]; [OWASP guidance][llm]). Code
outside the model decides whether a tool may run, and with what arguments, from the user's
authority, never from text in the content.

- Can retrieved text trigger a tool call? Require a per-task tool allowlist.
- Can a tool call carry data to the network? Require an egress allowlist.
- Which credential does the tool use? Least privilege, per user.
- "Be safe" in the prompt enforces nothing; the dispatcher's allow or deny must read the user's
  grants.

Test with a recording tool and a synthetic secret: feed a document that asks for the secret to be
posted and assert the post is refused.

[cwe-20]: https://cwe.mitre.org/data/definitions/20.html
[cwe-200]: https://cwe.mitre.org/data/definitions/200.html
[cwe-284]: https://cwe.mitre.org/data/definitions/284.html
[cwe-api]: https://cwe-api.mitre.org/api/v1/
[cvss31]: https://www.first.org/cvss/v3.1/specification-document
[cvss40]: https://www.first.org/cvss/v4.0/specification-document
[calc31]: https://www.first.org/cvss/calculator/3.1
[calc40]: https://www.first.org/cvss/calculator/4.0
[cwe-1427]: https://cwe.mitre.org/data/definitions/1427.html
[llm]: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
