import logging

from inventory._version import __version__

log = logging.getLogger(__name__)


def reserve(stock, sku, qty):
    """Reserve qty units of sku; stock maps sku -> units available."""
    if qty <= 0:
        raise ValueError("qty must be positive")
    if stock.get(sku, 0) < qty:
        log.info("insufficient stock for %s", sku)
        return False
    stock[sku] -= qty
    return True
