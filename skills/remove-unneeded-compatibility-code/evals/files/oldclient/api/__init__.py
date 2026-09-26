"""Tiny request router for the orders API."""


def parse_v2_header(value):
    """Parse 'application/vnd.acme.v2+json; region=eu' into a dict."""
    media, _, params = value.partition(";")
    out = {"version": 2}
    for part in params.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# Kept for old clients. (2019)
def parse_v1_header(value):
    """Parse 'acme-v1/eu' into a dict."""
    _, _, region = value.partition("/")
    return {"version": 1, "region": region or "us"}


def route(headers):
    accept = headers.get("Accept", "")
    if accept.startswith("acme-v1"):
        return parse_v1_header(accept)
    return parse_v2_header(accept)
