# Service rules

- All services log JSON via `services/shared/log.py`; never call print().
- Money is always integer cents; never use float for amounts.
- Search only: rebuild the index fixture with `python3 tools/build_index.py` after changing `schema.json`.
