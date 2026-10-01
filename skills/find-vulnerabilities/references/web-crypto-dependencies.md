# Web, crypto, and dependencies

## Contents

- [SSRF](#ssrf)
- [Authorization](#authorization)
- [Tokens](#tokens)
- [Randomness, passwords, comparison](#randomness-passwords-comparison)
- [Secrets and logs](#secrets-and-logs)
- [Dependencies](#dependencies)

## SSRF

For a server-side fetch of a URL from input (CWE-918; [OWASP][owasp-ssrf]):

- Require an allowed scheme and an exact allowlisted host, resolve it, and require every returned
  address (A and AAAA) to pass an IP policy such as `ipaddress` `is_global`. Checking the hostname
  string alone misses `127.1`, decimal or IPv6-mapped forms, and DNS names that resolve to internal
  addresses.
- Do not let the client follow redirects. `urllib` follows 301, 302, 303, 307, and 308 by default
  ([urllib][urllib]); read `Location`, resolve it, and re-run the full check for each hop.
- Connect to the IP that passed the check and send the original host in `Host`, because a second
  resolution can return another address (DNS rebinding). For HTTPS, wrap the socket with
  `server_hostname=host` so certificate verification still uses the name.

## Authorization

- Object level (CWE-639): every handler that loads a record by a client-supplied ID or slug must
  check on the server that this caller may do this action on this object, usually by owner or
  tenant. An unguessable ID is not a control. Answer like a missing record.
- Function level (CWE-862): each privileged action checks role or permission and scope on the
  server. Being logged in is not enough and hiding the button is not a control. Deny by default.
- Test both with two users in two tenants: user B requests user A's ID.

## Tokens

- JWT: require an explicit algorithm allowlist, validate issuer and audience and expiry, and never
  let the token header choose the key or accept `alg: none` ([RFC 8725][rfc8725]).
- OAuth: public clients using the authorization code grant need PKCE. A confidential client without
  PKCE is a hardening note; use of the implicit or password grant is a finding. Check `state` and
  exact redirect URI matching ([RFC 9700][rfc9700]).

## Randomness, passwords, comparison

- `random` (Mersenne Twister) is "completely unsuitable for cryptographic purposes"
  ([random][random]). Tokens, IDs, reset codes, and salts need `secrets.token_urlsafe(32)` or
  equivalent (CWE-338).
- Password storage: a salted memory-hard KDF, not SHA-256 or MD5, and not a bare hash with a global
  salt. `hashlib.scrypt` (n=2^17, r=8, p=1 is one OWASP minimum) or Argon2id (`argon2-cffi`
  `PasswordHasher`; m=47104 KiB, t=1, p=1 is one OWASP minimum; the stdlib has no Argon2)
  ([scrypt][scrypt]; [OWASP][owasp-pw]). Store algorithm, parameters, salt, and key together, and
  rehash on login when parameters change (CWE-916).
- Compare MACs, signatures, webhook digests, and reset tokens with `hmac.compare_digest`, not `==`
  ([compare][compare]; CWE-208). It can still leak length.

## Secrets and logs

- Scan the tree and history: `gitleaks dir --redact .` and `gitleaks git --redact .` (exit 1 on
  leaks; [gitleaks][gitleaks]); `trufflehog filesystem --no-verification .` as a second detector
  ([trufflehog][trufflehog]). Recommend rotating anything found in history in the report; deleting
  the line does not revoke it, and rotation is the owner's step, not yours.
- Logs must not carry tokens, passwords, session IDs, or full headers and bodies ([OWASP
  logging][owasp-log]). Redact known keys when building the record and add a `logging.Filter` as a
  last defense (CWE-532).

## Dependencies

- An advisory says a version is in an affected range. Report "affected version present,
  exploitability unverified" separately from a traced, reachable vulnerability.
- Audit tools: `cargo audit` (reads `Cargo.lock`, [RustSec][rustsec]), `bun audit` (reads
  `bun.lock`, exits 1 on findings, `--prod` limits to production paths, [docs][bun-audit]),
  `pip-audit -r requirements.txt` (PyPI by default; not a static analyzer, [docs][pip-audit]),
  `osv-scanner scan --offline --download-offline-databases -r .` (many ecosystems, sends no package
  data, [docs][osv]). `bun audit` and `pip-audit` send package names and versions to the registry.
- A new dependency in the diff: confirm the exact package name and registry from the project's
  official docs or source repository, then inspect publisher, release history, and install scripts.
  Code models recommend nonexistent package names, which attackers can register ([USENIX Security
  2025][usenix]).
- CI, signing, and release credentials: provenance states which source and builder produced an
  artifact ([SLSA][slsa]); an SBOM lists components and proves nothing about vulnerabilities.

[owasp-ssrf]: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
[urllib]: https://docs.python.org/3/library/urllib.request.html
[rfc8725]: https://www.rfc-editor.org/rfc/rfc8725
[rfc9700]: https://www.rfc-editor.org/rfc/rfc9700
[random]: https://docs.python.org/3/library/random.html
[scrypt]: https://docs.python.org/3/library/hashlib.html#hashlib.scrypt
[owasp-pw]: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
[compare]: https://docs.python.org/3/library/hmac.html#hmac.compare_digest
[gitleaks]: https://github.com/gitleaks/gitleaks
[trufflehog]: https://github.com/trufflesecurity/trufflehog
[owasp-log]: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
[rustsec]: https://rustsec.org/
[bun-audit]: https://bun.com/docs/pm/cli/audit
[pip-audit]: https://pypi.org/project/pip-audit/
[osv]: https://google.github.io/osv-scanner/usage/
[usenix]: https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen
[slsa]: https://slsa.dev/spec/v1.2/
