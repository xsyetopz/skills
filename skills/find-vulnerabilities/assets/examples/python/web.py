"""Server-side request forgery and authorization pairs.

``vulnerable_*`` functions are INTENTIONALLY VULNERABLE. The tests run them
against an ``http.server`` bound to 127.0.0.1 and inject a resolver and a
connector, so no packet leaves the machine.
"""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

IP = ipaddress.IPv4Address | ipaddress.IPv6Address
REDIRECTS = {301, 302, 303, 307, 308}


class BlockedRequest(Exception):
    """The destination failed the fetch policy."""


def system_resolve(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return sorted({str(info[4][0]) for info in infos})


def public_ip(ip: IP) -> bool:
    # Unwrap ::ffff:a.b.c.d so the IPv4 rules apply on every Python version.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connects to a validated IP but verifies the certificate for host."""

    def __init__(self, host: str, ip: str, port: int, context: ssl.SSLContext):
        super().__init__(host, port, timeout=5, context=context)
        self._ip = ip
        self._context = context

    def connect(self) -> None:
        raw = socket.create_connection((self._ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


def default_connect(
    scheme: str, host: str, ip: str, port: int
) -> http.client.HTTPConnection:
    if scheme == "https":
        context = ssl.create_default_context()
        return PinnedHTTPSConnection(host, ip, port, context)
    return http.client.HTTPConnection(ip, port, timeout=5)


@dataclass(frozen=True)
class FetchPolicy:
    allowed_hosts: frozenset[str]
    schemes: frozenset[str] = frozenset({"https"})
    resolve: Callable[[str, int], list[str]] = system_resolve
    ip_allowed: Callable[[IP], bool] = public_ip
    connect: Callable[[str, str, str, int], http.client.HTTPConnection] = field(
        default=default_connect
    )

    def check(self, url: str) -> tuple[str, str, str, int, str]:
        parts = urlsplit(url)
        host = parts.hostname or ""
        if parts.scheme not in self.schemes or host not in self.allowed_hosts:
            raise BlockedRequest(f"destination not allowed: {url!r}")
        port = parts.port or (443 if parts.scheme == "https" else 80)
        addresses = self.resolve(host, port)
        if not addresses:
            raise BlockedRequest(f"no address for {host!r}")
        for address in addresses:  # every A and AAAA answer must pass
            if not self.ip_allowed(ipaddress.ip_address(address)):
                raise BlockedRequest(f"{host!r} resolves to {address}")
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        return parts.scheme, host, addresses[0], port, path


# --- SSRF (CWE-918) ---------------------------------------------------------


def vulnerable_fetch(url: str) -> bytes:
    # INTENTIONALLY VULNERABLE (CWE-918): any scheme, host, or address.
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read()


def vulnerable_check_then_urlopen(url: str, policy: FetchPolicy) -> bytes:
    # INTENTIONALLY VULNERABLE (CWE-918): the check is right, but urlopen
    # resolves the name again and follows redirects without re-checking.
    policy.check(url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=5) as response:
        return response.read()


def fixed_fetch(url: str, policy: FetchPolicy, max_redirects: int = 3) -> bytes:
    for _ in range(max_redirects + 1):
        scheme, host, ip, port, path = policy.check(url)
        connection = policy.connect(scheme, host, ip, port)
        try:
            connection.request("GET", path, headers={"Host": host})
            response = connection.getresponse()
            location = response.getheader("Location")
            if response.status in REDIRECTS and location:
                url = urljoin(url, location)  # re-checked on the next pass
                continue
            return response.read()
        finally:
            connection.close()
    raise BlockedRequest("too many redirects")


# --- Authorization (CWE-639, CWE-862) ---------------------------------------


@dataclass(frozen=True)
class User:
    name: str
    tenant: str
    role: str = "member"


@dataclass(frozen=True)
class Invoice:
    tenant: str
    total: int


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


def vulnerable_get_invoice(
    store: dict[int, Invoice], user: User, invoice_id: int
) -> Invoice:
    # INTENTIONALLY VULNERABLE (CWE-639): authenticated, but the record is
    # chosen by a client-supplied key without an ownership check.
    del user
    return store[invoice_id]


def fixed_get_invoice(
    store: dict[int, Invoice], user: User, invoice_id: int
) -> Invoice:
    invoice = store.get(invoice_id)
    if invoice is None or invoice.tenant != user.tenant:
        raise NotFound(invoice_id)  # same answer as a missing record
    return invoice


def vulnerable_delete_user(users: dict[str, User], actor: User, name: str) -> None:
    # INTENTIONALLY VULNERABLE (CWE-862): any authenticated actor may call
    # this admin action; the UI merely hides the button.
    del actor
    users.pop(name)


def fixed_delete_user(users: dict[str, User], actor: User, name: str) -> None:
    target = users.get(name)
    if actor.role != "admin" or target is None or target.tenant != actor.tenant:
        raise Forbidden(name)
    users.pop(name)
