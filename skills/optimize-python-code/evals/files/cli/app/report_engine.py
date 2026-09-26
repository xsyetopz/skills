"""Report engine. Building the rate tables at import is expensive."""

import math


def _build_tables():
    table = {}
    for i in range(1, 2_000_000):
        table[i] = math.log(i) * math.sqrt(i)
    return table


RATES = _build_tables()


class ReportEngine:
    def __init__(self, scale: int = 1):
        self.scale = scale

    def render(self, ids):
        total = sum(RATES[i] for i in ids) * self.scale
        return f"report: {len(ids)} ids, weighted total {total:.3f}"
