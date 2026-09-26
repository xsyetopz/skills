"""Replaced versions kept only so the tests can compare behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar, TypeVar

from structure import Order

T = TypeVar("T")


class PriceFormatter(ABC):
    @abstractmethod
    def format(self, cents: int) -> str: ...


class SymbolPriceFormatter(PriceFormatter):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def format(self, cents: int) -> str:
        return f"{self.symbol}{cents // 100}.{cents % 100:02d}"


class PriceFormatterFactory:
    _symbols: ClassVar[dict[str, str]] = {"EUR": "€", "USD": "$"}

    def create(self, currency: str) -> PriceFormatter:
        return SymbolPriceFormatter(self._symbols[currency])


def format_price(cents: int, currency: str) -> str:
    return PriceFormatterFactory().create(currency).format(cents)


def shipping_label(order: Order) -> str:
    if order.paid:
        if order.items > 0:
            if order.address is not None:
                return f"ship {order.items} item(s) to {order.address}"
            else:
                return "hold: no address"
        else:
            return "hold: empty"
    else:
        return "hold: unpaid"


def chunks(items: Sequence[T], size: int) -> list[list[T]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    if len(items) == 0:
        return []
    if len(items) <= size:
        return [list(items)]
    result = [list(items[i : i + size]) for i in range(0, len(items) - size, size)]
    done = len(result) * size
    result.append(list(items[done:]))
    return result
