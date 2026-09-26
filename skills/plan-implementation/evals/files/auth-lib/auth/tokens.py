"""Signed session tokens."""

import hashlib
import hmac


def mk_tok(user_id: str, secret: bytes) -> str:
    sig = hmac.new(secret, user_id.encode(), hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def check_tok(token: str, secret: bytes) -> str | None:
    user_id, _, sig = token.rpartition(".")
    expected = hmac.new(secret, user_id.encode(), hashlib.sha256).hexdigest()
    return user_id if hmac.compare_digest(sig, expected) else None
