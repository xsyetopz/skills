"""In-memory customer store used by billing."""


class CustomerStore:
    def __init__(self):
        self._rows = {}

    def save(self, customer):
        self._rows[customer["customer_id"]] = dict(customer)

    def find(self, customer_id):
        """Return a copy of the customer, or None when the id is unknown."""
        row = self._rows.get(customer_id)
        return dict(row) if row is not None else None
