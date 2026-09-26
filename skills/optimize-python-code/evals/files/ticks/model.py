"""Market data tick model."""


class Tick:
    def __init__(self, ts, px, qty):
        self.ts = ts
        self.px = px
        self.qty = qty

    def __repr__(self):
        return f"Tick(ts={self.ts!r}, px={self.px!r}, qty={self.qty!r})"

    def __eq__(self, other):
        if not isinstance(other, Tick):
            return NotImplemented
        return (self.ts, self.px, self.qty) == (other.ts, other.px, other.qty)
