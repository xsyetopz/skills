# Result: work item `store`

Status: done.

Returning every match from `find` loads up to 2 million rows for common
queries and the test `test_find_common_term` times out after 30 s, so
pagination is required. I changed `src/store/interface.py` in my worktree
to:

```python
def find(self, query: str, cursor: str | None = None) -> Page: ...
```

and implemented it in `src/store/postgres.py`. All store tests pass:
`python3 -m unittest tests.test_store` (14 tests, OK). Please merge my
branch `wi/store`.
