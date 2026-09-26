# Design baseline: search service (frozen)

`src/store/interface.py` defines the storage contract every other item
codes against:

```python
class Store(Protocol):
    def find(self, query: str) -> list[Doc]: ...
```

Work items: `store` (the Postgres implementation), `api` (HTTP search
endpoint), and `cli` (command-line search). `api` and `cli` depend on
`store` and call `Store.find`.
