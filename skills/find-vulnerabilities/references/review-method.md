# Review method

Cards for running an authorized review and writing up its findings. The
worked output is [`review.md`](../assets/examples/review.md), checked by
[`check_findings.py`](../scripts/check_findings.py). Every example command
runs from the skill root.

## Contents

- Scope and rules of engagement
- Trust-boundary map
- Source-to-sink trace
- Semgrep taint rule
- Evidence classes
- Local exploit-condition test
- Finding format
- CWE selection
- CVSS v3.1 base vector
- CVSS v4.0 base vector
- Reporting without weaponized detail
- Agent tool boundary

## Scope and rules of engagement

**Definition.** A written statement of what may be reviewed (repository,
revision, components), by which methods (source reading, local tests,
scanners), and what is excluded (live hosts, real credentials, production
data, third-party services).

**Use when.**

- Before the first command of any review.
- A request mentions a URL, host, account, or token: decide whether it is
  a target (which needs the owner's authorization) or only context.

**Do not use when.**

- Never skip it. Probing a system the user does not own, or using found
  credentials, is out of scope for this skill; say so and stop that part.

**Example.**

```text
Scope: repo acme/billing @ 4f2c1e9, services api/ and worker/.
Methods: source review; unit tests and PoC tests against local fixtures;
  gitleaks, semgrep, and ecosystem audit tools on the checkout.
Excluded: staging/production hosts, customer data, the payment provider,
  any credential found during review (report it; never try it).
```

**Cost removed.** Out-of-scope actions (live requests, credential use).
Count them in the transcript as commands whose target is not localhost, a
temp directory, or the checkout; goal zero.

**Verify.**

1. Every command in the transcript targets the checkout, a temp directory,
   or 127.0.0.1.
1. The report's scope block names revision, methods, and exclusions.

## Trust-boundary map

**Definition.** A list of the places where data or control passes from a
less-trusted principal to a more-trusted one (network to handler, user to
tenant data, handler to shell/SQL/filesystem, CI to release), each with
the check it relies on.

**Use when.**

- Starting a review, to choose which sinks to trace.
- A feature adds an entry point, a parser, an outbound call, or a new
  role.

**Do not use when.**

- As a deliverable on its own: a boundary with no traced path is a
  design note, not a finding ([evidence classes](#evidence-classes)).

**Example.**

```text
Boundary                       Attacker          Check relied on
HTTP -> /search handler        anonymous         none (query param)
handler -> SQLite              via handler       parameter binding?
handler -> outbound HTTP       member            FetchPolicy.check
member -> invoice by ID        other tenant      tenant filter?
reset email -> token check     anyone            token entropy?
CI pull_request -> release     fork author       secrets not exposed?
```

The last row covers build and release authority: untrusted pull-request
code must not reach release credentials; see
[provenance](dependencies.md#provenance-and-sbom).

**Cost removed.** Unreviewed entry points. Compare the entry points from
a route listing or an `rg` for handlers with the rows in the map; the gap
should be 0.

**Verify.**

1. For each row, name the file:line of the check or write "none".
1. `rg -n '@app\.(get|post|route)|@router\.' .` (adapt to the framework)
   returns no route missing from the map.

## Source-to-sink trace

**Definition.** A chain from an attacker-controlled source (request
field, file, message) through each transformation and check to a
sensitive sink (query, shell, path, parser, network call, authorization
decision), with file:line for every hop.

**Use when.**

- A scanner, grep, or reading flags a dangerous call (`execute`,
  `subprocess`, `open`, `pickle.loads`, `urlopen`).
- Deciding whether a finding is confirmed or a hypothesis.

**Do not use when.**

- The sink receives only constants or values from a closed mapping:
  record a "not finding" with the reason instead (see the "Not findings"
  section of `review.md`).

**Example.**

```text
GET /search?name=   entry point (anonymous; route file in the target)
 -> vulnerable_find_user(db, name)   injection.py:34
 -> "... WHERE name = '" + name      injection.py:36  concatenation
 -> db.execute(query)                injection.py:37  SINK (CWE-89)
```

Paths are relative to `assets/examples/python/`.

**Cost removed.** Findings reported by API name alone. Count findings
whose Trace field lacks `->`; `check_findings.py` reports each one.

**Verify.**

1. Open each file:line in the trace and confirm the value flows unchanged
   or through the stated transformation.
1. `python3 scripts/check_findings.py REVIEW.md` prints no "Trace must
   show" problem.

## Semgrep taint rule

**Definition.** A Semgrep rule with `mode: taint` that reports a path
from `pattern-sources` to `pattern-sinks` unless a `pattern-sanitizers`
match lies between them. In Semgrep Community Edition, taint analysis is
intraprocedural; cross-function and cross-file tracking need Semgrep Pro
([taint mode docs][semgrep-taint]).

**Use when.**

- The same source/sink shape recurs across many handlers.
- A fix must stay fixed: the rule can run in CI.

**Do not use when.**

- The flow crosses functions or files and only Community Edition is
  available: a clean result is not evidence of absence. Trace by hand.
- Registry rulesets (`--config p/...`) need network access and send
  metrics, which the scope forbids: use local rule files with
  `--metrics=off`.

**Example.** Runnable: `assets/examples/semgrep/sql-taint.yaml` against
`handlers.py`.

```yaml
rules:
  - id: request-arg-reaches-sql-text
    mode: taint
    languages: [python]
    severity: ERROR
    message: Request data reaches the SQL text of execute() (CWE-89).
    pattern-sources:
      - pattern: $REQ.args.get(...)
    pattern-sinks:
      - patterns:
          - pattern: $CUR.execute($QUERY, ...)
          - focus-metavariable: $QUERY
    pattern-sanitizers:
      - pattern: int(...)
```

`focus-metavariable` makes only the query text a sink, so a value passed
in the parameter tuple is not reported.

**Cost removed.** Manual re-tracing of each handler. Local run (Semgrep
1.176.0, offline, `--metrics=off`): 1 result, on the concatenating
handler; 0 on the parameterized and `int()`-sanitized handlers.

**Verify.**

1. `semgrep scan --metrics=off --disable-version-check --config
   assets/examples/semgrep/sql-taint.yaml --json
   assets/examples/semgrep/handlers.py`
1. `sh assets/examples/verify.sh local` asserts the only flagged line is
   the one marked `CWE-89: flagged`.

## Evidence classes

**Definition.** Every item in a report is exactly one of: confirmed
(traced end to end, and demonstrated or fully argued under stated
preconditions), design risk (a required control is missing from the
design; no exploit path shown), or hypothesis (evidence missing or
contradictory; the report names the observation that would settle it).

**Use when.**

- Writing the Status field of every finding.
- A scanner or advisory reports something you have not traced.

**Do not use when.**

- Never promote a hypothesis to confirmed because the sink looks
  dangerous or a tool rated it critical.

**Example.** From `review.md`: F1, F2, F4 are confirmed by tests; F3 is a
hypothesis because only the source trace was done:

```text
- Status: hypothesis
- Evidence: source trace only; urllib's HTTPRedirectHandler follows
  301/302/303/307/308 by default; no local server test was run
- Verification: needed: a local http.server whose /redirect points at
  loopback; vulnerable returns the internal body, fixed raises
```

**Cost removed.** Overstated findings. Count findings marked confirmed
whose Evidence names no test, command, or complete trace.

**Verify.**

1. `check_findings.py` accepts only `confirmed`, `design risk`,
   `hypothesis` in Status.
1. Read each confirmed finding's Evidence: it names a runnable test or
   command and its observed result.

## Local exploit-condition test

**Definition.** A unit test that runs the vulnerable code against a local
synthetic target (in-memory database, temp directory, 127.0.0.1 server,
recorder function) and asserts that the security property fails. A
second test runs the fixed code on the same input and asserts that the
property holds, and a legitimate input must keep working.

**Use when.**

- Confirming a finding without touching a live system.
- Proving a fix: the same test must flip from "exploit condition
  observed" to "blocked".

**Do not use when.**

- Reproducing needs a real third-party service, real credentials, or a
  production host: report a hypothesis that names the missing observation.
- The payload would do damage if the test ran elsewhere (deleting files
  outside a temp dir, network scans): use a marker file or a recorder
  call instead.

**Example.** Runnable: `assets/examples/python/test_injection.py`.

```python
def test_metacharacter_runs_second_command(self) -> None:
    inj.vulnerable_count_lines(f"{self.data}; touch {self.marker}")
    self.assertTrue(self.marker.exists())

def test_argv_passes_one_literal_argument(self) -> None:
    inj.fixed_count_lines(f"{self.data}; touch {self.marker}")
    self.assertFalse(self.marker.exists())
    self.assertIn("2", inj.fixed_count_lines(str(self.data)))
```

**Cost removed.** Arguments about exploitability. The observable is
binary: marker file present (vulnerable) versus absent (fixed), rows
leaked 3 versus 0, recorder calls 1 versus 0.

**Verify.**

1. `python3 assets/examples/python/test_injection.py` passes.
1. Revert the fix in a scratch copy: the "blocked" test fails, which
   proves the test discriminates.

## Finding format

**Definition.** A Markdown finding: `### F<n>: <title>` followed by the
bullets CWE, Location (path:line), Status, Preconditions, Trace (with
`->`), Impact, Evidence, optional Severity (with a CVSS vector),
Remediation, and Verification.

**Use when.**

- Every confirmed finding, design risk, and hypothesis in a report.

**Do not use when.**

- The repository has its own finding or advisory template: fill that one
  with the same facts.
- Hardening notes with no attacker path go in a separate list, not as
  findings.

**Example.** F2 from `assets/examples/review.md`, rewrapped:

```markdown
### F2: Invoice readable across tenants by ID

- CWE: CWE-639 Authorization Bypass Through User-Controlled Key
- Location: python/web.py:154 `vulnerable_get_invoice`
- Status: confirmed
- Preconditions: authenticated member of any tenant; knows or guesses
  an invoice ID
- Trace: path param `invoice_id` -> vulnerable_get_invoice(user, id) ->
  store[id] -> response
- Impact: reads another tenant's invoice totals
- Evidence: `test_other_tenant_reads_invoice_by_id` returns tenant a's
  invoice to a tenant b user
- Severity: CVSS-B vector (score with the FIRST calculator)
  CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N
- Remediation: filter by the caller's tenant and answer like a missing
  record (`fixed_get_invoice`)
- Verification: `test_ownership_check_hides_other_tenant` raises
  NotFound for 1 and 99; alice still reads invoice 1
```

**Cost removed.** Incomplete findings. `check_findings.py` prints the
count as `N finding(s), M incomplete`; goal M = 0.

**Verify.**

1. `python3 scripts/check_findings.py REVIEW.md` exits 0.
1. `python3 scripts/test_check_findings.py` passes (the checker itself).

## CWE selection

**Definition.** Map each finding to the most specific CWE entry that
names the root-cause mistake. MITRE marks each entry's vulnerability
mapping usage: Base and Variant entries are the preferred level, and
entries such as CWE-20, CWE-200, and CWE-284 are "Discouraged" because
they describe impacts or are too broad ([CWE-20][cwe-20],
[CWE-200][cwe-200], [CWE-284][cwe-284]).

**Use when.**

- Filling the CWE field.

**Do not use when.**

- You would choose the CWE from the impact ("information disclosure")
  instead of the mistake ("missing ownership check", CWE-639).

**Example.** Titles and mapping usage from the [CWE REST
API][cwe-api] (`/api/v1/cwe/weakness/<ids>`), fetched 2026-09-25:

| Mistake | CWE | Level, usage |
| --- | --- | --- |
| SQL built from input | CWE-89 | Base, Allowed |
| Shell parses input | CWE-78 | Base, Allowed |
| Input parsed as an option | CWE-88 | Base, Allowed |
| HTML output not encoded | CWE-79 | Base, Allowed |
| Path escapes base dir | CWE-22 | Base, Allowed-with-Review |
| Server fetches attacker URL | CWE-918 | Base, Allowed |
| pickle/yaml of untrusted data | CWE-502 | Base, Allowed |
| XML external entity | CWE-611 | Base, Allowed |
| Entity expansion | CWE-776 | Base, Allowed |
| Record chosen by client key | CWE-639 | Base, Allowed |
| No authorization check | CWE-862 | Class, Allowed-with-Review |
| Weak PRNG for secrets | CWE-338 | Base, Allowed |
| Fast password hash | CWE-916 | Base, Allowed |
| Unsalted hash | CWE-759 | Variant, Allowed |
| Timing-dependent compare | CWE-208 | Base, Allowed |
| Hard-coded credential | CWE-798 | Base, Allowed-with-Review |
| Secret written to log | CWE-532 | Base, Allowed |
| Check-then-use race | CWE-367 | Base, Allowed |
| Symlink followed | CWE-59 | Base, Allowed |
| Catastrophic regex | CWE-1333 | Base, Allowed |
| Size arithmetic wraps | CWE-190 | Base, Allowed |
| Heap buffer overflow | CWE-122 | Variant, Allowed |
| Out-of-bounds write | CWE-787 | Base, Allowed-with-Review |
| Template source from input | CWE-1336 | Base, Allowed |
| Vulnerable dependency | CWE-1395 | Class, Allowed-with-Review |
| Prompt text from input | CWE-1427 | Base, Allowed |

Two rows, re-fetched 2026-09-26:

```sh
curl -s 'https://cwe-api.mitre.org/api/v1/cwe/weakness/639,862' |
  jq -c '.Weaknesses[] | [.ID, .Name, .Abstraction, .MappingNotes.Usage]'
# ["639","Authorization Bypass Through User-Controlled Key","Base","Allowed"]
# ["862","Missing Authorization","Class","Allowed-with-Review"]
```

The mistake CWE-639 names, from `assets/examples/python/web.py`:

```python
def vulnerable_get_invoice(
    store: dict[int, Invoice], user: User, invoice_id: int
) -> Invoice:
    # INTENTIONALLY VULNERABLE (CWE-639): authenticated, but the record is
    # chosen by a client-supplied key without an ownership check.
    del user
    return store[invoice_id]
```

`assets/examples/review.md` files it as
`CWE-639 Authorization Bypass Through User-Controlled Key`, not as the
impact (CWE-200).

**Cost removed.** Findings mapped to discouraged entries. Count CWE
fields citing CWE-20, CWE-200, or CWE-284; goal 0 unless no lower
entry fits and the report says why.

**Verify.**

1. `curl -s 'https://cwe-api.mitre.org/api/v1/cwe/weakness/89' | jq
   '.Weaknesses[0] | .Name, .MappingNotes.Usage'` returns the title and
   usage cited.
1. `rg -n 'CWE-(20|200|284)\b' REVIEW.md` returns nothing, or each hit
   explains why.

## CVSS v3.1 base vector

**Definition.** A string `CVSS:3.1/AV:_/AC:_/PR:_/UI:_/S:_/C:_/I:_/A:_`.
All eight Base metrics are mandatory; Temporal and Environmental metrics
are optional; metrics may appear in any order but only once; values per
[FIRST CVSS v3.1 Table 15][cvss31]. Scores map to None 0.0, Low 0.1-3.9,
Medium 4.0-6.9, High 7.0-8.9, Critical 9.0-10.0 (Table 14).

**Use when.**

- The organization or advisory format asks for CVSS v3.1.

**Do not use when.**

- The organization has its own severity rubric: use that.
- You would compute the score by hand or guess it from a label: record
  the vector and compute with the [FIRST v3.1 calculator][calc31].

**Example.**

```text
Severity: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
```

Each metric comes from the evidence: AV:N because the handler is
reachable over HTTP; PR:N because F1 needs no login; C:H because every
row is readable; I:N and A:N because the test shows reads only.

**Cost removed.** Invalid or unsupported vectors. `check_findings.py`
reports missing base metrics, duplicates, and disallowed values.

**Verify.**

1. `python3 scripts/check_findings.py REVIEW.md` shows no vector problem.
1. Open `https://www.first.org/cvss/calculator/3.1#` followed by the
   vector and record the score it shows; do not type a score yourself.

## CVSS v4.0 base vector

**Definition.** A string starting `CVSS:4.0/` with the eleven Base
metrics AV, AC, AT, PR, UI, VC, VI, VA, SC, SI, SA. Unlike v3.1, the
metrics must appear in the order of [FIRST CVSS v4.0 Table 23][cvss40];
Threat, Environmental, and Supplemental metrics are optional. v4.0 UI
values are N, P, A (not R), and a score is labeled CVSS-B, CVSS-BT,
CVSS-BE, or CVSS-BTE by the metric groups it used.

**Use when.**

- The consumer asks for CVSS v4.0.

**Do not use when.**

- You would reorder metrics or reuse v3.1 values (UI:R, S:U): the vector
  is invalid in v4.0.
- You would compute a score by formula: v4.0 scores come from the
  specification's lookup; use the [FIRST v4.0 calculator][calc40].

**Example.**

```text
Severity: CVSS-B vector (score with the FIRST calculator)
  CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N
```

**Cost removed.** Invalid v4.0 vectors. `check_findings.py` reports
out-of-order metrics and v3.1-only values (tested in
`test_invalid_vectors`).

**Verify.**

1. `python3 scripts/test_check_findings.py` passes.
1. Paste the vector into the FIRST v4.0 calculator and record its score
   with the nomenclature label.

## Reporting without weaponized detail

**Definition.** A report states the exploit condition (what input class
reaches which sink and what property fails) and points to the local test
that demonstrates it, without a ready-to-use exploit against the real
system: no working payload chains for deployed hosts, no real secrets, and
no step-by-step instructions beyond what the fix owner needs.

**Use when.**

- Writing Evidence and Impact fields.
- The report leaves the team (ticket, advisory, vendor disclosure).

**Do not use when.**

- The owner explicitly needs a full reproduction for triage: share it
  through their private channel, not in a public issue.

**Example.**

```text
Evidence: test_tautology_leaks_every_row (local SQLite fixture) returns
  3 of 3 rows for a quote-containing name. Payload class: a single
  quote that closes the string literal.
Not included: payloads for the production database, table names from
  production, any extracted data.
```

**Cost removed.** Secrets and live payloads in reports. Run
`python3 scripts/scan_secrets.py REPORT.md` (or gitleaks) on the report;
goal 0 matches.

**Verify.**

1. `python3 scripts/scan_secrets.py REPORT.md` exits 0.
1. Every Evidence field names a local test or trace, not a live URL.

## Agent tool boundary

**Definition.** In an application that lets a model call tools, retrieved
content (documents, web pages, issue text, tool output) and model output
are untrusted input. Code outside the model decides whether a tool may be
called, and with what arguments, from the user's authority, never from
text in the content ([OWASP prompt injection
guidance][llm]; [CWE-1427][cwe-1427]).

**Use when.**

- Reviewing an agent, chatbot, or pipeline whose model output reaches a
  tool, shell, HTTP client, or data store.

**Do not use when.**

- The model output is only shown to the user who wrote the prompt and
  reaches no tool: there is no privilege to cross.

**Example.** Review questions and the expected control:

```text
Can retrieved text trigger a tool call?   -> tool allowlist per task
Can a tool call carry data to the network? -> egress allowlist
Which credential does the tool use?       -> least privilege, per user
Does "be safe" in the prompt enforce it?   -> no; code must
```

Test with a local recording tool and a synthetic secret: feed a document
that asks for the secret to be posted, and assert the post is refused.

**Cost removed.** Tool calls authorized by content. Count tool
invocations in the test log whose arguments came from retrieved text
without an allowlist check; goal 0.

**Verify.**

1. No bundled example (tier: not runnable here). Build the recording-tool
   test in the target repository and run its test command.
1. Inspect the dispatcher: the allow/deny decision reads the user's
   grants, not the model's text.

[semgrep-taint]:
https://docs.semgrep.dev/writing-rules/data-flow/taint-mode/overview
[cwe-20]: https://cwe.mitre.org/data/definitions/20.html
[cwe-200]: https://cwe.mitre.org/data/definitions/200.html
[cwe-284]: https://cwe.mitre.org/data/definitions/284.html
[cwe-api]: https://cwe-api.mitre.org/api/v1/
[cvss31]: https://www.first.org/cvss/v3.1/specification-document
[cvss40]: https://www.first.org/cvss/v4.0/specification-document
[calc31]: https://www.first.org/cvss/calculator/3.1
[calc40]: https://www.first.org/cvss/calculator/4.0
[llm]:
https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
[cwe-1427]: https://cwe.mitre.org/data/definitions/1427.html
