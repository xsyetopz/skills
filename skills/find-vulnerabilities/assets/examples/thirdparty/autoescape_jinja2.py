"""Template autoescape pair with Jinja2 (CWE-79, CWE-1336).

Run: uv run --no-project --with jinja2 python autoescape_jinja2.py
Exits 0 when the vulnerable environment emits markup and the fixed one
does not.
"""

from __future__ import annotations

import jinja2  # pyright: ignore[reportMissingImports]

TEMPLATE = "<p>Hello, {{ name }}</p>"
PAYLOAD = "<script>alert(1)</script>"

# INTENTIONALLY VULNERABLE (CWE-79): Environment() defaults to
# autoescape=False, so values are inserted as raw markup.
vulnerable = jinja2.Environment()

fixed = jinja2.Environment(autoescape=True)

# INTENTIONALLY VULNERABLE (CWE-1336): user text used as template source.
ssti = jinja2.Environment(autoescape=True).from_string("{{ 7 * 7 }}")

# Fixed: the same user text passed as data stays literal.
as_data = jinja2.Environment(autoescape=True).from_string("{{ body }}")


def main() -> int:
    raw = vulnerable.from_string(TEMPLATE).render(name=PAYLOAD)
    safe = fixed.from_string(TEMPLATE).render(name=PAYLOAD)
    print("vulnerable:", raw)
    print("fixed:     ", safe)
    evaluated = ssti.render()
    literal = as_data.render(body="{{ 7 * 7 }}")
    print("user text as template source evaluates:", evaluated)
    print("user text as template data stays:", literal)
    ok = "<script>" in raw and "<script>" not in safe and "&lt;script&gt;" in safe
    ok = ok and evaluated == "49" and literal == "{{ 7 * 7 }}"
    print("jinja2", jinja2.__version__, "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
