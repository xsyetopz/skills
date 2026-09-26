# Repository instructions

Invoice service: a Python library in `src/invoice/` with unit tests in
`tests/`. Python 3.10+, standard library only.

## Commands

Run from the repository root:

```sh
python3 -m unittest discover -s tests -t .
python3 -m compileall -q src
```

Both must pass before a change is reported as done.

## Conventions

- Money is integer cents (`int`), never `float`; names end in `_cents`.
- Public functions live in `src/invoice/__init__.py`; everything else is
  private to its module (leading underscore).
- Tests mirror modules: `src/invoice/tax.py` is tested in
  `tests/test_tax.py`.

## Boundaries

- Do not edit `src/invoice/_rates_generated.py`; regenerate it with
  `python3 scripts/generate_rates.py` instead.
- Do not add dependencies; the library ships without any.
