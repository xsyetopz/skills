# Injection

Cards for input that becomes syntax in another interpreter: SQL, a shell,
a program's option parser, HTML, and templates. Runnable pairs live in
[`injection.py`](../assets/examples/python/injection.py) with tests in
`test_injection.py`; the Jinja2 cards run from `assets/examples/thirdparty/`.

Tier: **Executed** on Apple M1 Max, macOS, Python 3.14.7:
`python3 assets/examples/python/test_injection.py` ran 12 tests, OK.
Jinja2 3.1.6 ran through `uv run --with jinja2`.

## Contents

- SQL value parameters
- SQL identifier allowlist
- Argument vector instead of a shell
- End-of-options marker
- HTML text escaping
- Quoted attribute escaping
- URL scheme allowlist for links
- Template autoescape
- User text as template data, not template source

## SQL value parameters

**Definition.** Pass each value as a bound parameter (`?` or `:name` in
`sqlite3`, `%s` in psycopg) so the driver sends it as data that cannot
change the statement's syntax ([sqlite3 placeholders][sqlite-ph];
[OWASP SQL injection prevention][owasp-sqli]). Fixes CWE-89.

**Use when.**

- A query string is built with `+`, f-strings, `%`, or `.format()` and
  any operand can come from a request, file, message, or other user.

**Do not use when.**

- The dynamic part is an identifier (table, column, sort direction):
  placeholders bind values only; use the
  [identifier allowlist](#sql-identifier-allowlist).
- You would escape by hand instead: OWASP calls escaping fragile and
  database-specific.

**Example.**

```python
def vulnerable_find_user(db, name):
    query = "SELECT name, email FROM users WHERE name = '" + name + "'"
    return db.execute(query).fetchall()

def fixed_find_user(db, name):
    query = "SELECT name, email FROM users WHERE name = ?"
    return db.execute(query, (name,)).fetchall()
```

Runnable: `assets/examples/python/injection.py`.

**Cost removed.** Rows returned for the payload `x' OR '1'='1`: 3 of 3
(vulnerable) to 0 (fixed). A legitimate name with a quote (`o'brien`)
raises `OperationalError` only in the vulnerable version.

**Verify.**

1. `python3 assets/examples/python/test_injection.py
   SqlInjection.test_parameter_keeps_payload_as_data`
1. In the target, `rg -n 'execute\(\s*(f"|".*"\s*\+|.*%|.*\.format)'`
   lists remaining string-built queries; each needs a trace or a fix.

## SQL identifier allowlist

**Definition.** Map a user-chosen identifier (sort column, table) through
a dict of known-good values defined in code, reject anything else, and
turn direction into a boolean that selects `ASC` or `DESC` (OWASP SQL
injection prevention, "allow-list input validation").

**Use when.**

- `ORDER BY`, `GROUP BY`, a column list, or a table name depends on
  input.

**Do not use when.**

- The part is a value; bind it as a
  [parameter](#sql-value-parameters).

**Example.**

```python
SORT_COLUMNS = {"name": "name", "email": "email"}

def fixed_list_users(db, sort, descending=False):
    column = SORT_COLUMNS.get(sort)
    if column is None:
        raise ValueError(f"unsupported sort key: {sort!r}")
    direction = "DESC" if descending else "ASC"
    return db.execute(
        f"SELECT name FROM users ORDER BY {column} {direction}"
    ).fetchall()
```

**Cost removed.** Attacker SQL in the identifier slot: the subquery
payload runs in the vulnerable version (3 rows returned) and raises
`ValueError` in the fixed one.

**Verify.**

1. `python3 assets/examples/python/test_injection.py
   SqlInjection.test_identifier_injection_runs_attacker_expression`
1. Confirm by reading that the f-string's operands come only from
   `SORT_COLUMNS` values and the two literals, and record it as a "not
   finding".

## Argument vector instead of a shell

**Definition.** Call `subprocess.run([...])` with a list and the default
`shell=False`, so no shell parses the arguments and metacharacters such
as `;`, `|`, `$()` reach the program as literal bytes. With `shell=True`,
Python's subprocess docs make quoting the application's job
([security considerations][subprocess-sec]). Fixes CWE-78.

**Use when.**

- `shell=True`, `os.system`, `os.popen`, or a string command contains any
  non-constant part.

**Do not use when.**

- The program itself reads an argument as options or code (a `-` prefix,
  `sh -c`, `git -c`, `find -exec`): add the
  [end-of-options marker](#end-of-options-marker) or validate.
- The target is a Windows `.bat`/`.cmd` file: the docs warn it may run
  through a shell regardless of `shell=False`.

**Example.**

```python
def vulnerable_count_lines(path):
    command = "wc -l " + path
    return subprocess.run(command, shell=True, capture_output=True,
                          text=True, check=False).stdout

def fixed_count_lines(path):
    return subprocess.run(["wc", "-l", "--", path], capture_output=True,
                          text=True, check=False).stdout
```

**Cost removed.** Marker file created by `data.txt; touch MARKER`: yes
(vulnerable) to no (fixed), with the legitimate count unchanged.

**Verify.**

1. `python3 assets/examples/python/test_injection.py CommandInjection`
1. `rg -n 'shell=True|os\.system|os\.popen' .` in the target: each hit
   gets a trace to its inputs.

## End-of-options marker

**Definition.** Put `--` before operands that come from input, so a value
starting with `-` is not parsed as an option. POSIX Utility Syntax
Guideline 10 defines the first `--` as the end of options
([POSIX guidelines][posix-args]); `argparse`, `getopt`, and most CLIs
follow it. Fixes CWE-88.

**Use when.**

- An argv list passes user text to a program whose options read files,
  run commands, or change output (`--exec`, `-o`, `--upload-pack`, `-e`).

**Do not use when.**

- The program does not honor `--` (check its manual): validate the value
  against a pattern that cannot start with `-` instead.

**Example.** The child is a small argparse program with a dangerous
`--exec` option.

```python
def vulnerable_lookup(name):
    argv = [sys.executable, "-c", CHILD, name]
    return subprocess.run(argv, capture_output=True, text=True).stdout

def fixed_lookup(name):
    argv = [sys.executable, "-c", CHILD, "--", name]
    return subprocess.run(argv, capture_output=True, text=True).stdout
```

**Cost removed.** The value `--exec=payload` selects the option (`RAN`)
in the vulnerable version and arrives as a name (`NAMES --exec=payload`)
in the fixed one.

**Verify.**

1. `python3 assets/examples/python/test_injection.py ArgumentInjection`
1. For each argv built from input, confirm `--` precedes the operand or
   the program's manual says it has no options.

## HTML text escaping

**Definition.** `html.escape(s)` replaces `&`, `<`, `>`, and (with the
default `quote=True`) `"` and `'` with character references, so input
placed between tags is text, not markup ([html.escape][html-escape];
[OWASP XSS prevention][owasp-xss]). Fixes CWE-79 in the HTML body
context.

**Use when.**

- Code builds HTML with f-strings or concatenation and inserts
  user-controlled text between tags.

**Do not use when.**

- A template engine with autoescape already renders the value; escaping
  again double-encodes (`&amp;lt;`).
- The value goes into a URL, `<script>`, `style`, or an event-handler
  attribute: each context has its own rule (see the next two cards; OWASP
  forbids untrusted data in script and style blocks outside quoted data
  values).

**Example.**

```python
def vulnerable_greeting(name):
    return f"<p>Hello, {name}</p>"

def fixed_greeting(name):
    return f"<p>Hello, {html.escape(name)}</p>"
```

**Cost removed.** `<script>` elements produced from the payload, counted
by `html.parser`: 1 (vulnerable) to 0 (fixed).

**Verify.**

1. `python3 assets/examples/python/test_injection.py
   CrossSiteScripting.test_text_context`
1. Parse the output with an HTML tokenizer, as the test does; do not
   check for the substring `<script>` alone.

## Quoted attribute escaping

**Definition.** For a value inside a quoted attribute, escape the quote
characters too: `html.escape(value, quote=True)`. With `quote=False`, a
`"` in the value ends the attribute and the rest becomes new attributes.
OWASP requires quoted attributes and an encoded value.

**Use when.**

- User text goes into `value="..."`, `title="..."`, `alt="..."`, or
  another non-URL, non-event attribute.

**Do not use when.**

- The attribute is unquoted: quote it first; escaping alone cannot stop
  a space from starting a new attribute.
- The attribute is `href`, `src`, `action`, or `on*`: see the
  [URL scheme allowlist](#url-scheme-allowlist-for-links); never place
  input in event handlers.

**Example.**

```python
def vulnerable_input_value(value):
    v = html.escape(value, quote=False)
    return f'<input name="q" value="{v}">'

def fixed_input_value(value):
    v = html.escape(value, quote=True)
    return f'<input name="q" value="{v}">'
```

**Cost removed.** Attributes on the parsed element for the payload
`" autofocus onfocus="alert(1)`: `onfocus` present (vulnerable) versus
exactly `{name, value}` with the payload intact as the value (fixed).

**Verify.**

1. `python3 assets/examples/python/test_injection.py
   CrossSiteScripting.test_attribute_context`
1. `rg -n 'quote=False' .` in the target; each hit must not feed an
   attribute.

## URL scheme allowlist for links

**Definition.** Before placing input in `href` or `src`, parse it with
`urllib.parse.urlsplit`, allow only the schemes the feature needs
(`http`, `https`), then HTML-escape it. Escaping alone leaves
`javascript:` URLs working; OWASP says to validate URL schemes in these
attributes.

**Use when.**

- Profile links, redirects rendered as links, markdown-to-HTML output,
  or any user-supplied URL rendered into markup.

**Do not use when.**

- The URL is a server-side redirect target: that is an open-redirect
  check (CWE-601) against an allowlist of destinations, not a scheme
  check.

**Example.**

```python
SAFE_LINK_SCHEMES = {"http", "https"}

def fixed_profile_link(url):
    if urlsplit(url.strip()).scheme.lower() not in SAFE_LINK_SCHEMES:
        return "<span>site</span>"
    return f'<a href="{html.escape(url)}">site</a>'
```

`strip()` and `lower()` matter: the test payload is
`" JavaScript:alert(1)"`, which browsers still treat as a script URL.

**Cost removed.** `href` values starting with `javascript:` after
parsing: 1 (vulnerable) to 0 (fixed); an `https` URL with a query string
survives unchanged.

**Verify.**

1. `python3 assets/examples/python/test_injection.py
   CrossSiteScripting.test_url_context`
1. Add `data:` and `vbscript:` cases in the target's test if its sink
   accepts them.

## Template autoescape

**Definition.** The template engine HTML-escapes every inserted value
unless the template explicitly marks it safe. Jinja2's `Environment()`
escapes only when you pass `autoescape=True` or a callable such as
`select_autoescape(...)` ([Jinja2 API][jinja-autoescape]); the local run
below shows the default leaves markup raw.

**Use when.**

- Reviewing any server-side template setup: find where the environment
  is created and what `autoescape` is set to.
- Templates contain `|safe`, `Markup(...)`, `{% autoescape false %}`,
  `mark_safe`, React `dangerouslySetInnerHTML`, or Angular
  `bypassSecurityTrust*`: each is an escape hatch to trace.

**Do not use when.**

- The output is not HTML (plain-text email, JSON): HTML escaping
  corrupts it; use the format's own encoder.

**Example.** Runnable: `assets/examples/thirdparty/autoescape_jinja2.py`.

```python
TEMPLATE = "<p>Hello, {{ name }}</p>"
vulnerable = jinja2.Environment()
fixed = jinja2.Environment(autoescape=True)
```

**Cost removed.** Local run (Jinja2 3.1.6): the vulnerable environment
renders `<script>alert(1)</script>` verbatim; the fixed one renders
`&lt;script&gt;alert(1)&lt;/script&gt;`.

**Verify.**

1. `uv run --no-project --with jinja2 python
   assets/examples/thirdparty/autoescape_jinja2.py` prints `PASS`.
1. `rg -n 'Environment\(|autoescape|\|safe|Markup\(|mark_safe' .` in the
   target; trace every escape hatch to its input.

## User text as template data, not template source

**Definition.** Pass user text to `render(name=...)` as data, never to
`from_string`, `Template(...)`, or `render_template_string` as template
source, where it runs as template code (CWE-1336).

**Use when.**

- Code constructs a template from user text (custom email bodies,
  "preview" features, error pages that echo the path).

**Do not use when.**

- The feature must let users write templates: use a sandboxed
  environment and review that design separately.

**Example.** From `autoescape_jinja2.py`: the source `{{ 7 * 7 }}`
renders `49`, which proves expression evaluation without doing anything
harmful.

```python
ssti = jinja2.Environment(autoescape=True).from_string("{{ 7 * 7 }}")
assert ssti.render() == "49"
as_data = jinja2.Environment(autoescape=True).from_string("{{ body }}")
assert as_data.render(body="{{ 7 * 7 }}") == "{{ 7 * 7 }}"
```

**Cost removed.** Expressions evaluated from user text: `{{ 7 * 7 }}`
yields `49` as source and stays literal as data.

**Verify.**

1. Run the Jinja2 example above; it prints the evaluated `49` line.
1. `rg -n 'from_string\(|render_template_string\(|Template\(' .` in the
   target; each argument must be a constant or a trusted file.

[sqlite-ph]:
https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
[owasp-sqli]:
https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
[subprocess-sec]:
https://docs.python.org/3/library/subprocess.html#security-considerations
[posix-args]:
https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap12.html
[html-escape]: https://docs.python.org/3/library/html.html#html.escape
[owasp-xss]:
https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
[jinja-autoescape]: https://jinja.palletsprojects.com/en/stable/api/#autoescaping
