"""Function-shape refactorings: each baseline_* and candidate_* pair behaves
identically (see test_examples.py) while the candidate has lower nesting,
cyclomatic complexity, or parameter count as measured by lizard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class OrderError(ValueError):
    """An order failed validation; the message names the rule."""


# --- Guard clauses -------------------------------------------------------


def baseline_ship_order(order: Mapping[str, object]) -> str:
    if order.get("paid"):
        if order.get("items"):
            if order.get("address"):
                if not order.get("cancelled"):
                    return "shipped"
                else:
                    raise OrderError("order is cancelled")
            else:
                raise OrderError("order has no address")
        else:
            raise OrderError("order has no items")
    else:
        raise OrderError("order is not paid")


def candidate_ship_order(order: Mapping[str, object]) -> str:
    if not order.get("paid"):
        raise OrderError("order is not paid")
    if not order.get("items"):
        raise OrderError("order has no items")
    if not order.get("address"):
        raise OrderError("order has no address")
    if order.get("cancelled"):
        raise OrderError("order is cancelled")

    return "shipped"


# --- Phases: validate, prepare, execute ----------------------------------


def baseline_invoice_total(lines: list[dict[str, object]], tax_rate: float) -> int:
    total = 0
    for line in lines:
        if "price_cents" in line and "quantity" in line:
            price = line["price_cents"]
            quantity = line["quantity"]
            if isinstance(price, int) and isinstance(quantity, int):
                if price >= 0 and quantity > 0:
                    total += price * quantity
                else:
                    raise ValueError("negative price or non-positive quantity")
            else:
                raise ValueError("price and quantity must be integers")
        else:
            raise ValueError("line is missing price_cents or quantity")
    return round(total * (1 + tax_rate))


@dataclass(frozen=True)
class InvoiceLine:
    price_cents: int
    quantity: int


def parse_invoice_line(raw: dict[str, object]) -> InvoiceLine:
    if "price_cents" not in raw or "quantity" not in raw:
        raise ValueError("line is missing price_cents or quantity")
    price = raw["price_cents"]
    quantity = raw["quantity"]
    if not isinstance(price, int) or not isinstance(quantity, int):
        raise ValueError("price and quantity must be integers")
    if price < 0 or quantity <= 0:
        raise ValueError("negative price or non-positive quantity")
    return InvoiceLine(price_cents=price, quantity=quantity)


def candidate_invoice_total(lines: list[dict[str, object]], tax_rate: float) -> int:
    parsed = [parse_invoice_line(raw) for raw in lines]

    subtotal_cents = sum(line.price_cents * line.quantity for line in parsed)

    return round(subtotal_cents * (1 + tax_rate))


# --- Nested conditional expressions --------------------------------------


def baseline_shipping_band(weight_grams: int) -> str:
    return (
        "letter"
        if weight_grams <= 100
        else "small"
        if weight_grams <= 2000
        else "medium"
        if weight_grams <= 10000
        else "freight"
    )


_SHIPPING_BANDS = ((100, "letter"), (2000, "small"), (10000, "medium"))


def candidate_shipping_band(weight_grams: int) -> str:
    for upper_limit_grams, band in _SHIPPING_BANDS:
        if weight_grams <= upper_limit_grams:
            return band
    return "freight"


# --- Parameter object ----------------------------------------------------


def baseline_connect_url(
    host: str,
    port: int,
    user: str,
    database: str,
    use_tls: bool,
    timeout_ms: int,
    application_name: str,
) -> str:
    scheme = "postgresqls" if use_tls else "postgresql"
    return (
        f"{scheme}://{user}@{host}:{port}/{database}"
        f"?connect_timeout_ms={timeout_ms}&application_name={application_name}"
    )


@dataclass(frozen=True)
class ConnectionSettings:
    host: str
    port: int
    user: str
    database: str
    use_tls: bool
    timeout_ms: int
    application_name: str


def candidate_connect_url(settings: ConnectionSettings) -> str:
    scheme = "postgresqls" if settings.use_tls else "postgresql"
    return (
        f"{scheme}://{settings.user}@{settings.host}:{settings.port}/"
        f"{settings.database}?connect_timeout_ms={settings.timeout_ms}"
        f"&application_name={settings.application_name}"
    )


# --- Dispatch table instead of an if/elif chain ---------------------------


def baseline_apply(op: str, left: int, right: int) -> int:
    if op == "add":
        return left + right
    elif op == "sub":
        return left - right
    elif op == "mul":
        return left * right
    elif op == "min":
        return min(left, right)
    elif op == "max":
        return max(left, right)
    else:
        raise KeyError(op)


_OPERATIONS = {
    "add": lambda left, right: left + right,
    "sub": lambda left, right: left - right,
    "mul": lambda left, right: left * right,
    "min": min,
    "max": max,
}


def candidate_apply(op: str, left: int, right: int) -> int:
    operation = _OPERATIONS[op]  # KeyError for unknown op, as before
    return operation(left, right)


# --- Explaining variables ------------------------------------------------


def baseline_can_retry(status: int, attempt: int, elapsed_ms: int) -> bool:
    return (
        (status == 429 or 500 <= status < 600) and attempt < 5 and elapsed_ms < 30_000
    )


def candidate_can_retry(status: int, attempt: int, elapsed_ms: int) -> bool:
    is_retryable_status = status == 429 or 500 <= status < 600
    has_attempts_left = attempt < 5
    is_within_deadline = elapsed_ms < 30_000
    return is_retryable_status and has_attempts_left and is_within_deadline


# --- Boolean flag argument -----------------------------------------------


def baseline_format_amount(cents: int, compact: bool) -> str:
    if compact:
        return f"{cents / 100:.0f}"
    return f"{cents / 100:,.2f}"


def format_amount(cents: int) -> str:
    return f"{cents / 100:,.2f}"


def format_amount_compact(cents: int) -> str:
    return f"{cents / 100:.0f}"
