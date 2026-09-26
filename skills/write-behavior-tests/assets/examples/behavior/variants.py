"""Named replacements for attributes of subjects.py.

alt_* conform to the stated contracts and must pass every good test.
bug_* break one contract and must fail the tests named in
expectations.json. Some bug_* pass the weak tests on purpose.
"""

from __future__ import annotations

import base64
from collections import Counter
from pathlib import Path

import subjects


# --- conforming alternatives ----------------------------------------------
class CountingCart:
    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()

    def add(self, item: str) -> None:
        self._counts[item] += 1

    def remove(self, item: str) -> None:
        if not self._counts[item]:
            raise ValueError(item)
        self._counts[item] -= 1

    @property
    def total(self) -> int:
        return sum(subjects.PRICES[i] * n for i, n in self._counts.items())


class CountingBasket:
    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()

    def add(self, item: str) -> None:
        self._counts[item] += 1

    def count(self, item: str) -> int:
        return self._counts[item]


def invoice_total_by_addition(price: int, quantity: int, discount: int) -> int:
    total = 0
    for _ in range(quantity):
        total += price
    return total - discount


def price_for_direct(item: str, catalog):
    return catalog[item]


def render_name_inline(text: str) -> str:
    return text.strip()


def notify_guard(address, allowed, send):
    if allowed:
        send(address, "ready")
    return allowed


ALTERNATIVES = {
    "alt_counting_cart": {"Cart": CountingCart},
    "alt_counting_basket": {"Basket": CountingBasket},
    "alt_invoice_addition": {"invoice_total": invoice_total_by_addition},
    "alt_price_direct": {"price_for": price_for_direct},
    "alt_render_inline": {"render_name": render_name_inline},
    "alt_notify_guard": {"notify": notify_guard},
    "alt_fees_tuple": {"DELIVERY_FEES": (5,)},
}


# --- deliberate faults ----------------------------------------------------
def shipping_charges_zero(weight_kg: float) -> int:
    if weight_kg < 0:
        raise ValueError("weight must not be negative")
    return 5


class CartRemoveNoop(subjects.Cart):
    def remove(self, item: str) -> None:
        pass


class ConnectionNoReopen(subjects.Connection):
    def __init__(self) -> None:
        super().__init__()
        self._closed_once = False

    def open(self) -> None:
        if not self._closed_once:
            self.is_open = True

    def close(self) -> None:
        self.is_open = False
        self._closed_once = True


def invoice_ignores_discount(price: int, quantity: int, discount: int) -> int:
    return price * quantity


def accept_percentage_off_by_one(value: int) -> bool:
    return 1 <= value < 100


def can_edit_suspended_editor(role: str, account: str) -> bool:
    return role in {"admin", "editor"} and account in {"active", "suspended"}


def next_state_skip_review(state: str, event: str) -> str:
    if (state, event) == ("draft", "approve"):
        return "published"
    return subjects.next_state(state, event)


_WRONG = str.maketrans("+/", "-_")


def b64encode_urlsafe(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii").translate(_WRONG)


def b64decode_urlsafe(text: str) -> bytes:
    return base64.b64decode(text.translate(str.maketrans("-_", "+/")))


def render_report_unsorted(rows, generated_at):
    lines = [f"generated: {generated_at}", "name,count"]
    lines += [f"{name},{count}" for name, count in rows]
    return "\n".join(lines) + "\n"


def render_name_ignores_trim(text: str) -> str:
    subjects._trim(text)
    return text


class BasketCountsOnce(subjects.Basket):
    def count(self, item: str) -> int:
        return min(1, super().count(item))


def price_for_zero(item, catalog):
    if item not in catalog:
        raise KeyError(item)
    catalog[item]
    return 0


def notify_sends_when_denied(address, allowed, send):
    send(address, "ready")
    return allowed


def notify_never_sends(address, allowed, send):
    return allowed


class UsersCaseSensitive(subjects.Users):
    def __init__(self, connection) -> None:
        self.db = connection
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            " id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE)"
        )


def split_fields_drops_empty(line: str) -> list[str]:
    return [part for part in line.split(":") if part]


def write_config_truncates_first(path: Path, text: str) -> None:
    path.write_text("", encoding="utf-8")
    if "=" not in text:
        raise ValueError("config must contain key=value lines")
    path.write_text(text, encoding="utf-8")


class AccountNoLock(subjects.Account):
    def __init__(self) -> None:
        super().__init__()
        self._lock = _NoLock()


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class SessionWallClock(subjects.Session):
    """Ignores the injected clock for expiry: reads real time instead."""

    def __init__(self, ttl, clock):
        import time

        super().__init__(ttl, clock)
        self.expires_at = time.monotonic() + ttl
        self.clock = time.monotonic


def delivery_fee_six(distance_km: int) -> int:
    return 6


MUTANTS = {
    "bug_shipping_zero": {"shipping": shipping_charges_zero},
    "bug_cart_remove_noop": {"Cart": CartRemoveNoop},
    "bug_connection_no_reopen": {"Connection": ConnectionNoReopen},
    "bug_invoice_no_discount": {"invoice_total": invoice_ignores_discount},
    "bug_percentage_off_by_one": {"accept_percentage": accept_percentage_off_by_one},
    "bug_can_edit_suspended": {"can_edit": can_edit_suspended_editor},
    "bug_state_skip_review": {"next_state": next_state_skip_review},
    "bug_b64_urlsafe": {
        "b64encode": b64encode_urlsafe,
        "b64decode": b64decode_urlsafe,
    },
    "bug_report_unsorted": {"render_report": render_report_unsorted},
    "bug_render_ignores_trim": {"render_name": render_name_ignores_trim},
    "bug_basket_counts_once": {"Basket": BasketCountsOnce},
    "bug_price_zero": {"price_for": price_for_zero},
    "bug_notify_when_denied": {"notify": notify_sends_when_denied},
    "bug_notify_never": {"notify": notify_never_sends},
    "bug_users_case_sensitive": {"Users": UsersCaseSensitive},
    "bug_split_drops_empty": {"split_fields": split_fields_drops_empty},
    "bug_config_truncates": {"write_config": write_config_truncates_first},
    "bug_account_no_lock": {"Account": AccountNoLock},
    "bug_session_wall_clock": {"Session": SessionWallClock},
    "bug_fee_six": {"delivery_fee": delivery_fee_six},
}

VARIANTS = {**ALTERNATIVES, **MUTANTS}
