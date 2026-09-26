# Security review: example service in assets/examples/python

Scope: the `vulnerable_*` code paths in `injection.py`, `web.py`, and
`crypto.py`, treated as one internal HTTP service. Authorized method:
source review plus local tests against in-memory or temporary targets.
Not in scope: live systems, credentials, and deployment configuration.
Revision: the files as checked in next to this review.

Trust boundaries: HTTP request (anonymous or authenticated member) to
handler; handler to SQLite; handler to outbound HTTP; handler to the
password-reset mailer.

## Findings

### F1: SQL injection in user lookup

- CWE: CWE-89 Improper Neutralization of Special Elements used in an SQL
  Command ('SQL Injection')
- Location: python/injection.py:37 `vulnerable_find_user`
- Status: confirmed
- Preconditions: caller can supply `name`; no other precondition
- Trace: request `name` -> vulnerable_find_user(name) -> string concat ->
  db.execute(query)
- Impact: any caller reads every row of `users` (3 of 3 in the fixture)
- Evidence: `test_tautology_leaks_every_row` returns 3 rows; a quote in a
  legitimate name raises `OperationalError`
- Severity: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N (base metrics
  only; score it with the FIRST calculator)
- Remediation: bind `name` as a `?` parameter (`fixed_find_user`)
- Verification: `test_parameter_keeps_payload_as_data` returns 0 rows for the
  payload and bob's row for "bob"

### F2: Invoice readable across tenants by ID

- CWE: CWE-639 Authorization Bypass Through User-Controlled Key
- Location: python/web.py:154 `vulnerable_get_invoice`
- Status: confirmed
- Preconditions: authenticated member of any tenant; knows or guesses an invoice
  ID
- Trace: path param `invoice_id` -> vulnerable_get_invoice(user, id) ->
  store[id] -> response
- Impact: reads another tenant's invoice totals
- Evidence: `test_other_tenant_reads_invoice_by_id` returns tenant a's invoice
  to a tenant b user
- Severity: CVSS-B vector (score with the FIRST calculator)
  CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N
- Remediation: filter by the caller's tenant and answer like a missing record
  (`fixed_get_invoice`)
- Verification: `test_ownership_check_hides_other_tenant` raises NotFound for 1
  and 99; alice still reads invoice 1

### F3: Outbound fetch follows redirects after a one-time check

- CWE: CWE-918 Server-Side Request Forgery (SSRF)
- Location: python/web.py:103 `vulnerable_check_then_urlopen`
- Status: hypothesis
- Preconditions: attacker controls a response from an allowlisted host (open
  redirect or compromise)
- Trace: request `url` -> FetchPolicy.check(url) -> opener.open(url) ->
  HTTPRedirectHandler -> internal address
- Impact: a response from an allowed host could steer the fetch to an internal
  address
- Evidence: source trace only; urllib's HTTPRedirectHandler follows
  301/302/303/307/308 by default; no local server test was run in this review
- Remediation: re-run the policy on every hop and connect to the checked address
  (`fixed_fetch`)
- Verification: needed: a local http.server whose /redirect points at loopback;
  vulnerable returns the internal body, fixed raises BlockedRequest

### F4: Password-reset token derived from the clock

- CWE: CWE-338 Use of Cryptographically Weak Pseudo-Random Number Generator
  (PRNG)
- Location: python/crypto.py:23 `vulnerable_reset_token`
- Status: confirmed
- Preconditions: attacker requests a reset for a victim and knows the request
  time to within a minute
- Trace: reset request time -> random.Random(int(now)) -> getrandbits(128) ->
  emailed token
- Impact: the token is one of 121 candidates for a one-minute window, so the
  reset link can be forged
- Evidence: `test_clock_seeded_token_is_recomputed_from_a_time_window` finds the
  token among the candidates
- Severity: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N (score with the
  FIRST calculator)
- Remediation: `secrets.token_urlsafe(32)` (`fixed_reset_token`)
- Verification: `test_secrets_token_is_not_in_the_window` passes

## Not findings

- `fixed_list_users` builds SQL with an f-string, but only from the
  `SORT_COLUMNS` values and a fixed ASC/DESC choice; no request text
  reaches the SQL string.

## Checks run

- `python3 assets/examples/python/test_injection.py`, `test_web.py`,
  `test_crypto.py`: all pass; the vulnerable half of each pair shows the
  exploit condition.
- `python3 scripts/check_findings.py assets/examples/review.md`: 4
  findings, 0 incomplete.
