# Web requests and access control

Cards for server-side request forgery and for authorization at the
object and function level. Runnable code:
[`web.py`](../assets/examples/python/web.py), tests in `test_web.py`.

Tier, per part (Apple M1 Max, macOS, Python 3.14.7):

- **Executed**: `public_ip`, `FetchPolicy.check` with an injected
  resolver, and all authorization pairs (`test_web.py`, 7 tests, OK).
- **Compiled only** (ruff and pyright clean, not run by the bundled
  tests): the network paths of `vulnerable_fetch`,
  `vulnerable_check_then_urlopen`, `fixed_fetch`, and
  `PinnedHTTPSConnection`. Each SSRF card's Verify section says how to
  run them against a local `http.server`.

## Contents

- Host allowlist and resolved-address check
- Re-check every redirect hop
- Connect to the checked address
- Pinned HTTPS with hostname verification
- Object-level authorization
- Function-level authorization
- Token validation at the boundary

## Host allowlist and resolved-address check

**Definition.** Before an outbound request whose URL comes from input,
require an allowed scheme and an exact allowlisted host, resolve the
host, and require every returned address (A and AAAA) to pass an IP
policy such as `ipaddress` `is_global`. OWASP prefers an allowlist and
resolved-address checks ([OWASP SSRF][owasp-ssrf]). Fixes CWE-918.

**Use when.**

- Webhooks, URL previews, image fetchers, import-from-URL, PDF
  renderers, or any `urlopen`, `requests.get`, `httpx`, or `curl` call
  whose URL or host is influenced by a user.

**Do not use when.**

- The feature can take an identifier instead of a URL (a partner key
  mapped to a fixed endpoint): build the URL on the server and parse no
  user URLs at all.
- You would write a deny-list of hostnames or IP spellings: alternate
  encodings and DNS make it incomplete; check resolved addresses.

**Example.**

```python
def public_ip(ip):
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global

# FetchPolicy.check, condensed
parts = urlsplit(url)
host = parts.hostname or ""
if parts.scheme not in self.schemes or host not in self.allowed_hosts:
    raise BlockedRequest(f"destination not allowed: {url!r}")
for address in self.resolve(host, port):
    if not self.ip_allowed(ipaddress.ip_address(address)):
        raise BlockedRequest(f"{host!r} resolves to {address}")
```

`urlopen` also accepts `file:` and `data:` URLs because `FileHandler`
and `DataHandler` are default handlers ([urllib.request][urllib]); the
scheme allowlist closes that. Python 3.13 changed `is_private` and
`is_global` for several ranges and made IPv4-mapped IPv6 follow the
IPv4 rules ([ipaddress][ipaddress]); the explicit unwrap keeps older
versions correct.

**Cost removed.** Destinations accepted by the policy: 11 of 11
non-public addresses rejected (loopback, RFC 1918, 169.254.169.254,
100.64/10, `::1`, `fd00::/8`, `fe80::/10`, mapped loopback and metadata);
2 of 2 public addresses allowed; `http:`, `file:`, lookalike hosts, and a
mixed public/private answer rejected.

**Verify.**

1. `python3 assets/examples/python/test_web.py PublicIp PolicyCheck`
1. Network path (compiled only here): start
   `http.server.HTTPServer(("127.0.0.1", 0), ...)` in a test, call
   `vulnerable_fetch` on its `/internal` path (returns the body), then
   `fixed_fetch` with the default policy (raises `BlockedRequest`).

## Re-check every redirect hop

**Definition.** Do not let the HTTP client follow redirects itself. Read
the `Location` header, resolve it against the current URL, and run the
full policy check again before the next request. `urllib`'s
`HTTPRedirectHandler` is installed by default and follows 301, 302,
303, 307, and 308 (the `http_error_30x` methods present in Python
3.14.7); OWASP says to disable redirect following.

**Use when.**

- A policy check runs once before `urlopen`, or before another client
  whose redirect behavior you have not confirmed in its docs.

**Do not use when.**

- The feature needs no redirects: disable them in the client and treat
  3xx as an error, which is simpler than re-checking.

**Example.**

```python
def fixed_fetch(url, policy, max_redirects=3):
    for _ in range(max_redirects + 1):
        scheme, host, ip, port, path = policy.check(url)
        connection = policy.connect(scheme, host, ip, port)
        try:
            connection.request("GET", path, headers={"Host": host})
            response = connection.getresponse()
            location = response.getheader("Location")
            if response.status in REDIRECTS and location:
                url = urljoin(url, location)  # re-checked next pass
                continue
            return response.read()
        finally:
            connection.close()
    raise BlockedRequest("too many redirects")
```

**Cost removed.** Hops that skip the policy: every hop after the first
in `vulnerable_check_then_urlopen`; 0 in `fixed_fetch`.

**Verify.**

1. Compiled only here. To execute: serve `/redirect` answering 302 with
   `Location: http://localhost:PORT/internal` on 127.0.0.1; with a
   policy allowing only host `127.0.0.1`, the vulnerable function
   returns the internal body and `fixed_fetch` raises `BlockedRequest`.
1. `rg -n 'allow_redirects|follow_redirects|HTTPRedirectHandler' .` in
   the target shows how each client handles 3xx.

## Connect to the checked address

**Definition.** Open the TCP connection to the exact IP address that
passed the policy, sending the original host in the `Host` header,
instead of handing the hostname to a client that resolves it again. A
second resolution can return a different address (DNS rebinding); OWASP
gives this as the reason to validate every resolved address and pin it.

**Use when.**

- The policy resolves the name, then a library connects by name.
- TTL-0 or attacker-controlled DNS is in the threat model (any
  user-supplied hostname).

**Do not use when.**

- An egress proxy or firewall enforces the address policy at connection
  time: verify that control instead and record where it lives.

**Example.**

```python
def default_connect(scheme, host, ip, port):
    if scheme == "https":
        context = ssl.create_default_context()
        return PinnedHTTPSConnection(host, ip, port, context)
    return http.client.HTTPConnection(ip, port, timeout=5)
```

`FetchPolicy.check` returns `(scheme, host, ip, port, path)`;
`test_returns_checked_address_for_pinning` asserts that the returned
address is the one that passed.

**Cost removed.** Name resolutions per request: 2 (check, then the
client's lookup) to 1.

**Verify.**

1. `python3 assets/examples/python/test_web.py
   PolicyCheck.test_returns_checked_address_for_pinning`
1. To execute the connection path: inject a resolver that returns a
   documentation address first and a connector that records the IP it
   is asked to dial and refuses anything but 127.0.0.1; assert the
   recorded list equals the checked address and the resolver ran once.

## Pinned HTTPS with hostname verification

**Definition.** Subclass `http.client.HTTPSConnection` so `connect()`
opens a socket to the checked IP and wraps it with
`context.wrap_socket(raw, server_hostname=host)`. TLS still verifies the
certificate against the hostname (SNI and name check), so pinning the IP
does not weaken verification ([ssl
wrap_socket][ssl-wrap]).

**Use when.**

- The allowed destinations use HTTPS and you connect to the checked
  address.

**Do not use when.**

- You would pass the IP as the host to a plain `HTTPSConnection`:
  verification then checks the certificate against the IP and fails, and
  the usual "fix", disabling verification, is a new vulnerability.

**Example.**

```python
class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, ip, port, context):
        super().__init__(host, port, timeout=5, context=context)
        self._ip = ip
        self._context = context

    def connect(self):
        raw = socket.create_connection((self._ip, self.port),
                                       self.timeout)
        self.sock = self._context.wrap_socket(
            raw, server_hostname=self.host)
```

**Cost removed.** Verification bypasses: 0 `CERT_NONE` or
`check_hostname = False` needed to pin.

**Verify.**

1. Compiled only here. To execute: create a self-signed certificate for
   `svc.example.test` with `openssl req -x509 -newkey rsa:2048 -nodes
   -subj /CN=svc.example.test -addext
   subjectAltName=DNS:svc.example.test`, serve HTTPS on 127.0.0.1, and
   trust it with `ssl.create_default_context(cafile=...)`; the fetch
   succeeds for `svc.example.test` and raises
   `ssl.SSLCertVerificationError` for another allowlisted name mapped to
   the same IP.
1. `rg -n 'CERT_NONE|check_hostname *= *False|verify=False' .` in the
   target returns nothing.

## Object-level authorization

**Definition.** Every operation that takes a client-supplied object key
(ID, slug, file name) loads the object and checks on the server that the
caller may perform this action on this object, usually by owner or
tenant. A missing or unguessable ID is not a control; OWASP requires the
check on every request ([OWASP authorization][owasp-authz]). Fixes
CWE-639.

**Use when.**

- Handlers read, update, delete, or export by ID: `/invoices/{id}`,
  batch endpoints, GraphQL resolvers, background jobs started by users.

**Do not use when.**

- One layer that every path must pass (query scope, row-level security,
  middleware) already enforces the check: test that layer, including
  batch and background paths, instead of repeating the check in every
  helper.

**Example.**

```python
def vulnerable_get_invoice(store, user, invoice_id):
    return store[invoice_id]

def fixed_get_invoice(store, user, invoice_id):
    invoice = store.get(invoice_id)
    if invoice is None or invoice.tenant != user.tenant:
        raise NotFound(invoice_id)  # same answer as a missing record
    return invoice
```

Answering "not found" in both cases hides which IDs exist; if the
application already answers 403, keep its policy.

**Cost removed.** Other-tenant invoices readable by ID: 1 of 1
(vulnerable) to 0; the owner still reads it.

**Verify.**

1. `python3 assets/examples/python/test_web.py
   Authorization.test_ownership_check_hides_other_tenant`
1. In the target, for each route with an ID parameter, a test logs in as
   tenant B and requests tenant A's object; it must get the not-found or
   forbidden response and no object data.

## Function-level authorization

**Definition.** Each privileged action checks the caller's role or
permission, and scope such as tenant, on the server. Being logged in is
not enough, and neither is hiding the UI. Deny by default. Fixes
CWE-862.

**Use when.**

- Admin, moderator, billing, export, or configuration endpoints; any
  route guarded only by `login_required` or equivalent.

**Do not use when.**

- The route is meant for every authenticated user: write that decision
  down so the next reviewer does not re-report it.

**Example.**

```python
def vulnerable_delete_user(users, actor, name):
    users.pop(name)

def fixed_delete_user(users, actor, name):
    target = users.get(name)
    if (actor.role != "admin" or target is None
            or target.tenant != actor.tenant):
        raise Forbidden(name)
    users.pop(name)
```

**Cost removed.** Admin actions a member can perform: 1 (vulnerable) to
0; an admin of another tenant is also refused; an admin in the same
tenant succeeds.

**Verify.**

1. `python3 assets/examples/python/test_web.py
   Authorization.test_role_and_tenant_checked_on_admin_action`
1. List routes and their guards; each privileged route names a
   permission check, verified by a test with a non-privileged user.

## Token validation at the boundary

**Definition.** A bearer token grants nothing until the service
validates it against the protocol's rules. For JWTs, RFC 8725 requires an
explicit algorithm allowlist and validation of issuer and audience, and warns
against letting token headers choose keys ([RFC 8725][rfc8725]). For
OAuth, RFC 9700 requires PKCE for public clients using the authorization
code grant and recommends it for confidential clients, and advises
against the implicit and resource-owner password grants
([RFC 9700][rfc9700]).

**Use when.**

- Code decodes JWTs, accepts OAuth tokens, or implements login
  callbacks.

**Do not use when.**

- The service delegates token checks to a gateway: verify the gateway
  configuration and that the service cannot be reached around it.

**Example.** Review checklist and the calls to look for:

```text
jwt.decode(token, key, algorithms=["RS256"], audience=AUD, issuer=ISS)
  - algorithms is a fixed list, never read from the token header
  - "none" is never in the list
  - audience and issuer are checked; exp/nbf are not disabled
  - key comes from configuration, not from a jku/x5u URL in the token
OAuth public client: authorization code + PKCE (S256)
ID token used only for login, never as an API access token
```

**Cost removed.** Token checks skipped: count `verify_signature: False`,
`algorithms=None`, or decode calls without `audience` in the target.

**Verify.**

1. No bundled example (tier: not runnable here; the stdlib has no JWT
   library). Run the target's token tests with a token signed by a wrong
   key, an `alg: none` token, and a token for another audience; each
   must be rejected.
1. `rg -n 'jwt\.decode|verify_signature|algorithms' .` in the target.

[owasp-ssrf]:
https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
[urllib]: https://docs.python.org/3/library/urllib.request.html
[ipaddress]:
https://docs.python.org/3/library/ipaddress.html#ipaddress.IPv4Address.is_private
[ssl-wrap]:
https://docs.python.org/3/library/ssl.html#ssl.SSLContext.wrap_socket
[owasp-authz]:
https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
[rfc8725]: https://www.rfc-editor.org/rfc/rfc8725
[rfc9700]: https://www.rfc-editor.org/rfc/rfc9700
