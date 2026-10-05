# Code Patterns

Python examples; the failure and the check carry over to other languages. Sources are linked per
section.

## Contents

- [SQL](#sql)
- [Shell and Argument Injection](#shell-and-argument-injection)
- [HTML and Templates](#html-and-templates)
- [File Paths, Tar, and Races](#file-paths-tar-and-races)
- [Deserialization](#deserialization)
- [XML](#xml)

## SQL

- Bind every value (`?` or `:name` in `sqlite3`, `%s` in psycopg), never `+`, f-strings, `%`, or
  `.format()` (CWE-89; [OWASP][owasp-sqli]).
- Placeholders cannot bind identifiers. Map a user-chosen column or table through a dict in code and
  turn direction into a boolean that picks `ASC` or `DESC`; reject anything else. Quoting an
  identifier from input is not a control.

## Shell and Argument Injection

- `subprocess.run([...])` with a list and the default `shell=False` passes `;`, `|`, `$()` as
  literal bytes. `shell=True`, `os.system`, and `os.popen` make quoting your job
  ([subprocess][subprocess-sec]; CWE-78).
- A list does not stop option injection: an operand starting with `-` is parsed as an option
  (`git log -- "$ref"`, `curl -- "$url"`). Put `--` before operands from input, where the tool
  supports it (CWE-88).

## HTML and Templates

- `html.escape(s)` escapes `&`, `<`, `>`, and with `quote=True` (the default) `"` and `'`. Between
  tags that suffices; inside a quoted attribute `quote=False` lets `"` start new attributes
  ([html.escape][html-escape]; CWE-79).
- Escaping does not neutralize `javascript:` in `href` or `src`. Parse with `urllib.parse.urlsplit`,
  allow only `http` and `https`, then escape.
- Jinja2 `Environment()` does not autoescape by default. Pass `autoescape=True` or
  `select_autoescape(...)` ([Jinja2][jinja-autoescape]). Treat `|safe` and `Markup(...)` on input as
  findings.
- Never pass user text to `from_string`, `Template(...)`, or `render_template_string` as source;
  pass it to `render(name=...)` as data (CWE-1336).

## File Paths, Tar, and Races

- Containment: `Path.resolve()` both the base and the joined candidate (it follows symlinks and
  removes `..`), then require `candidate.is_relative_to(base)`. A `startswith` string check on the
  path passes `/srv/uploads-evil` for `/srv/uploads` (CWE-22).
- `tarfile.extractall(path, filter="data")` blocks members that leave the destination, unsafe links,
  and device files. Filters exist from Python 3.12 and in some backports
  (`hasattr(tarfile, "data_filter")`); 3.14 made `"data"` the default. Older runtimes extract
  unsafely ([tarfile filters][tar-filter]).
- `os.path.exists`, `os.access`, or `is_symlink` followed by `open` is a time-of-check race, which
  the `os.access` docs call a security hole ([os.access][os-access]). On POSIX, open once with
  `os.open(p, os.O_RDONLY | os.O_NOFOLLOW)` (`O_NOFOLLOW` does not exist on Windows) and check the
  descriptor with `os.fstat` and `stat.S_ISREG` (CWE-367, CWE-59).
- Create files with `os.open(p, O_WRONLY | O_CREAT | O_EXCL, 0o600)` or `tempfile.mkstemp`; `O_EXCL`
  fails on an existing path, including a symlink ([POSIX open][posix-open]).

## Deserialization

- `pickle.loads` on bytes that cross a trust boundary runs code: "Only unpickle data you trust"
  ([pickle][pickle]). Use `json.loads` and validate the shape. If the format must stay pickle,
  subclass `pickle.Unpickler` and override `find_class` to allow an explicit list and raise
  `UnpicklingError` otherwise. `shelve` also uses pickle.
- `yaml.safe_load` builds plain types. `yaml.load(..., Loader=yaml.Loader)` or `UnsafeLoader`, and
  `yaml.unsafe_load`, honor `!!python/object/apply` tags. PyYAML 5.4 moved those tags to
  `UnsafeLoader` and 6.0 made `Loader` mandatory, so `yaml.load(text)` without a loader is an error
  in 6.x, not a safe default ([PyYAML CHANGES][pyyaml]).

## XML

- Reject DOCTYPE where the format allows none. In Java set
  `http://apache.org/xml/features/disallow-doctype-decl` to `true` on `DocumentBuilderFactory`,
  `SAXParserFactory`, and `XMLInputFactory` equivalents ([OWASP XXE][owasp-xxe]; CWE-611, CWE-776).
- Python's SAX stopped resolving external general entities by default in 3.7.1;
  `feature_external_ges` turns that back on ([xml.sax][sax]). In stdlib Expat, raise from
  `StartDoctypeDeclHandler` to refuse DTDs.
- Expat below 2.7.2 may be vulnerable to billion laughs, quadratic blowup, and large tokens; check
  `pyexpat.EXPAT_VERSION` ([XML security][xml-sec]). `defusedxml` raises `EntitiesForbidden` by
  default and `DTDForbidden` with `forbid_dtd=True` ([defusedxml][defusedxml]).

[owasp-sqli]: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
[subprocess-sec]: https://docs.python.org/3/library/subprocess.html#security-considerations
[html-escape]: https://docs.python.org/3/library/html.html#html.escape
[jinja-autoescape]: https://jinja.palletsprojects.com/en/stable/api/#autoescaping
[tar-filter]: https://docs.python.org/3/library/tarfile.html#tarfile-extraction-filter
[os-access]: https://docs.python.org/3/library/os.html#os.access
[posix-open]: https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html
[pickle]: https://docs.python.org/3/library/pickle.html#restricting-globals
[pyyaml]: https://github.com/yaml/pyyaml/blob/main/CHANGES
[owasp-xxe]: https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html
[sax]: https://docs.python.org/3/library/xml.sax.html
[xml-sec]: https://docs.python.org/3/library/xml.html#xml-security
[defusedxml]: https://github.com/tiran/defusedxml
