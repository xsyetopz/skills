# Files and parsers

Cards for filesystem boundaries (paths, archives, check-then-use races)
and for parsers that can do more than parse (pickle, YAML, XML). Runnable
pairs: [`files.py`](../assets/examples/python/files.py),
[`parsers.py`](../assets/examples/python/parsers.py),
[`yaml_loading.py`](../assets/examples/python/yaml_loading.py),
[`Xxe.java`](../assets/examples/java/Xxe.java), and
[`defused_xml.py`](../assets/examples/thirdparty/defused_xml.py).

Tier: **Executed** on Apple M1 Max, macOS, Python 3.14.7 with Expat
2.7.4, PyYAML 6.0.3 (validation venv), OpenJDK 25.0.4.1, defusedxml 0.7.1
(through uv). `test_files.py` ran 10 tests and `test_parsers.py` 9 tests,
OK. The POSIX-only tests skip where `os.O_NOFOLLOW` is missing.

## Contents

- Resolved path containment
- Tar extraction data filter
- No-follow open, then check the descriptor
- Exclusive create
- JSON instead of pickle
- Restricted unpickler
- YAML safe loader
- SAX external entities left off
- Reject DOCTYPE in stdlib expat
- Java disallow-doctype-decl
- Expat amplification limit
- defusedxml

## Resolved path containment

**Definition.** Resolve the base directory and the joined candidate with
`Path.resolve()` (which follows symlinks and removes `..`), then require
`candidate.is_relative_to(base)` (Python 3.9+,
[pathlib][pathlib-rel]). Fixes CWE-22.

**Use when.**

- A request, archive entry, or message supplies a file name or relative
  path that is joined to a directory.

**Do not use when.**

- An attacker can create or replace symlinks inside the base directory
  between the check and the open: the check is then a TOCTOU race; add the
  [no-follow open](#no-follow-open-then-check-the-descriptor) or open
  relative to a directory descriptor.
- You would check a string prefix: `/srv/public_evil` starts with
  `/srv/public` (`test_prefix_string_check_is_not_containment`).

**Example.**

```python
def vulnerable_read(root, name):
    return Path(os.path.join(root, name)).read_bytes()

def fixed_read(root, name):
    base = root.resolve()
    target = (base / name).resolve()
    if not target.is_relative_to(base):
        raise PermissionError(f"outside {base}: {name!r}")
    return target.read_bytes()
```

`os.path.join(root, "/etc/x")` discards `root`; the tests also cover
absolute names and a symlink inside the root.

**Cost removed.** Reads outside the base. The vulnerable version was
tried with `../secret.txt` and an absolute path and read 2 of 2; the fixed
one raises on 4 of 4 (those two, `a/../../secret.txt`, and an in-root
symlink).

**Verify.**

1. `python3 assets/examples/python/test_files.py PathTraversal`
1. In the target, `rg -n 'os\.path\.join|/ *request|send_file|open\('` and
   trace each path operand to its source.

## Tar extraction data filter

**Definition.** `TarFile.extractall(path, filter="data")` refuses members
whose resolved path leaves the destination, absolute or outside links,
and device files, and strips dangerous mode bits. Filters exist since
Python 3.12 and in some backports (test with
`hasattr(tarfile, "data_filter")`); Python 3.14 made `"data"` the
default ([tarfile extraction filters][tar-filter]). Fixes CWE-22.

**Use when.**

- Code extracts an uploaded or downloaded tar archive.
- The project supports Python below 3.14: pass `filter="data"`
  explicitly, because earlier defaults honor `../` names.

**Do not use when.**

- You need resource limits: the docs say `data` does not stop denial of
  service (size, member count), duplicate names, or case-insensitive
  clashes; count and size members yourself.
- The archive is a zip: `zipfile` has no filter; check each
  `ZipInfo.filename` with
  [resolved path containment](#resolved-path-containment).

**Example.**

```python
def vulnerable_extract(archive, dest):
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="fully_trusted")

def fixed_extract(archive, dest):
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="data")
```

**Cost removed.** Files written outside `dest` from a member named
`../escaped.txt`: 1 (vulnerable) to 0; the fixed call raises
`tarfile.OutsideDestinationError`.

**Verify.**

1. `python3 assets/examples/python/test_files.py ArchiveExtraction`
1. `rg -n 'extractall|extract\(' .` in the target: each call names
   `filter="data"` or runs only on trusted archives (state why).

## No-follow open, then check the descriptor

**Definition.** Open once with `os.open(path, os.O_RDONLY |
os.O_NOFOLLOW)`, which fails if the final path component is a symlink,
then check the opened file with `os.fstat` and `stat.S_ISREG`. The check
and the use refer to the same open file, so nothing can be swapped in
between. The `os.access` docs call check-then-open a security hole
([os.access][os-access]). Fixes CWE-367 and CWE-59.

**Use when.**

- A privileged process opens a path in a directory that a less
  privileged user can write (upload spools, `/tmp`, shared volumes).
- Code calls `os.access`, `is_symlink`, `exists`, or `stat` on a path and
  then opens the same path.

**Do not use when.**

- Intermediate directories are attacker-writable: `O_NOFOLLOW` guards
  only the last component. macOS offers `os.O_NOFOLLOW_ANY` (Python
  3.10+); elsewhere open each component with `dir_fd`.
- The code runs on Windows: `O_NOFOLLOW` is Unix-only.

**Example.** The `between` hook runs the attacker's swap at the race
point, so the race reproduces on every run.

```python
def vulnerable_read_upload(path, between=_noop):
    if path.is_symlink() or not path.is_file():
        raise PermissionError(f"not a regular file: {path}")
    between()
    return path.read_bytes()

def fixed_read_upload(path, between=_noop):
    between()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise PermissionError(f"not a regular file: {path}")
        return handle.read()
```

**Cost removed.** Secret bytes returned after a swap to a symlink:
present (vulnerable) to `OSError` (fixed).

**Verify.**

1. `python3 assets/examples/python/test_files.py CheckThenUse`
1. In the target, list check-then-use pairs with `rg -n
   'os\.access|\.exists\(\)|is_symlink|os\.path\.isfile'` and read the
   next use of the same path.

## Exclusive create

**Definition.** Create files with `os.open(path, O_WRONLY | O_CREAT |
O_EXCL, 0o600)` (or `tempfile.mkstemp`). POSIX requires `open` with
`O_CREAT | O_EXCL` to fail with `EEXIST` if the path exists, including
when it is a symlink ([POSIX open][posix-open]). Fixes CWE-367 and
CWE-59 for file creation.

**Use when.**

- Code checks `exists()` and then writes, in a directory others can
  write.
- Code uses predictable temp names (`/tmp/app-report.txt`).

**Do not use when.**

- The code is meant to overwrite an existing file: write a temp file
  with `mkstemp` in the same directory and `os.replace` it.

**Example.**

```python
def vulnerable_create_report(path, text, between=_noop):
    if path.exists():
        raise FileExistsError(path)
    between()
    path.write_text(text)

def fixed_create_report(path, text, between=_noop):
    between()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
```

**Cost removed.** Target file overwritten through a planted symlink:
yes (vulnerable) to `FileExistsError` with the target unchanged (fixed).

**Verify.**

1. `python3 assets/examples/python/test_files.py
   CheckThenUse.test_exclusive_create_refuses_planted_symlink`
1. `rg -n "open\(.*['\"]w" .` near an `exists()` check in the target.

## JSON instead of pickle

**Definition.** Replace `pickle.loads` on data that crosses a trust
boundary with a data-only format such as `json.loads`, then validate the
shape. The pickle docs: "The pickle module is not secure. Only unpickle
data you trust", because a stream can import and call any global
([pickle][pickle]). Fixes CWE-502.

**Use when.**

- `pickle.load(s)`, `shelve`, or a library that unpickles internally
  reads bytes from a request, cookie, queue, a cache shared with other
  tenants, or a downloaded file.

**Do not use when.**

- The bytes never leave a trust boundary you control and are signed
  (the pickle docs suggest `hmac` to detect tampering): document the key
  handling instead of switching formats.

**Example.**

```python
def vulnerable_load_session(blob):
    return pickle.loads(blob)

def fixed_load_session(blob):
    data = json.loads(blob)
    if not isinstance(data, dict):
        raise ValueError("session must be a JSON object")
    return data
```

The test payload is a class whose `__reduce__` returns
`(parsers.record_call, ("ran",))`: loading it calls a list-append
recorder, which proves arbitrary-callable execution without running
anything harmful.

**Cost removed.** Recorder calls during load: 1 (vulnerable) to 0 (fixed
raises `ValueError`).

**Verify.**

1. `python3 assets/examples/python/test_parsers.py Deserialization`
1. `rg -n 'pickle\.loads?|cPickle|shelve\.open|joblib\.load|torch\.load'
   .` in the target and trace each input.

## Restricted unpickler

**Definition.** Subclass `pickle.Unpickler` and override `find_class` to
return only globals from an explicit allowlist and raise
`UnpicklingError` for anything else, as in the pickle docs' "Restricting
Globals" section.

**Use when.**

- The format must stay pickle (existing stored data) and the allowed
  types are few and known.

**Do not use when.**

- JSON or another data-only format is an option: the docs warn "you
  have to be careful with what you allow"; each allowed callable is
  attack surface. Never allow `builtins.eval`, `getattr`, `os.*`,
  `subprocess.*`, or `importlib.*`.

**Example.**

```python
SAFE_GLOBALS = {("builtins", "set"), ("builtins", "frozenset")}

class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in SAFE_GLOBALS:
            return getattr(builtins, name)
        raise pickle.UnpicklingError(f"global {module}.{name} is forbidden")
```

**Cost removed.** Recorder calls: 0, and the load raises
`UnpicklingError`; a pickled `{1, 2}` still loads.

**Verify.**

1. `python3 assets/examples/python/test_parsers.py
   Deserialization.test_restricted_unpickler_forbids_unlisted_globals`
1. Read the allowlist: each entry is a data type, not a callable with
   side effects.

## YAML safe loader

**Definition.** `yaml.safe_load(text)` builds only plain YAML types.
`yaml.load(text, Loader=yaml.UnsafeLoader)` (or `yaml.unsafe_load`)
honors `!!python/object/apply` tags and calls the named function. PyYAML
5.4 moved those tags to `UnsafeLoader` (CVE-2020-14343), and 6.0 made the
`Loader` argument mandatory ([PyYAML CHANGES][pyyaml]). Fixes CWE-502.

**Use when.**

- Any `yaml.load(..., Loader=yaml.Loader|UnsafeLoader)` or
  `yaml.unsafe_load` on configuration, uploads, or messages not fully
  controlled by the operator.
- PyYAML below 5.4 is resolved in the lockfile: `FullLoader` there is
  also unsafe; upgrade.

**Do not use when.**

- The file is operator-owned configuration that legitimately needs
  Python tags; document that trust decision instead.

**Example.** Runnable with PyYAML installed (the test skips otherwise).

```python
def vulnerable_load(text):
    return yaml.load(text, Loader=yaml.UnsafeLoader)

def fixed_load(text):
    return yaml.safe_load(text)
```

**Cost removed.** For `!!python/object/apply:parsers.record_call
['ran']`: 1 recorder call (vulnerable) versus `ConstructorError`
(fixed), and plain YAML loads unchanged. Local PyYAML 6.0.3 also rejected
the tag under `FullLoader`.

**Verify.**

1. `~/.cache/xsyetopz-skills/validation-venv/bin/python
   assets/examples/python/test_parsers.py YamlLoading` (any Python with
   PyYAML).
1. `rg -n 'yaml\.(load|unsafe_load|load_all)\(' .` in the target.

## SAX external entities left off

**Definition.** Python's SAX parser stopped processing external general
entities by default in 3.7.1; turning
`xml.sax.handler.feature_external_ges` on lets a document read local
files or URLs ([xml.sax][sax]; [feature_external_ges][sax-ges]). Fixes
CWE-611.

**Use when.**

- Code calls `setFeature(feature_external_ges, True)` or uses a
  third-party parser (lxml `resolve_entities=True`, `XMLParser(...)`
  with `load_dtd`) on untrusted XML.

**Do not use when.**

- The parser is stdlib ElementTree or minidom: locally both refused to
  expand the external entity (ElementTree raised "undefined entity";
  minidom returned an empty element). Their risk is entity expansion;
  see the [Expat amplification limit](#expat-amplification-limit).

**Example.**

```python
def _sax_text(document, external_entities):
    handler = _Text()  # a ContentHandler that collects characters()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_external_ges,
                      external_entities)
    parser.parse(io.StringIO(document))
    return handler.text

def vulnerable_sax_text(document):
    return _sax_text(document, external_entities=True)

def fixed_sax_text(document):
    return _sax_text(document, external_entities=False)
```

**Cost removed.** Synthetic secret file contents in the parsed text:
present (vulnerable) to empty string (fixed).

**Verify.**

1. `python3 assets/examples/python/test_parsers.py ExternalEntities`
1. `rg -n 'feature_external_ges|resolve_entities|load_dtd|no_network'
   .` in the target.

## Reject DOCTYPE in stdlib expat

**Definition.** Set `StartDoctypeDeclHandler` on an
`xml.parsers.expat` parser to a function that raises, so the parser
refuses any document with a DTD before entities are declared. This is the stdlib
equivalent of disabling DTDs, which the OWASP XXE cheat sheet calls the
safest prevention ([OWASP XXE][owasp-xxe]). Fixes CWE-611 and CWE-776.

**Use when.**

- The format never needs a DTD (most APIs, configs, SAML after schema
  validation) and defusedxml is not available.

**Do not use when.**

- Documents legitimately carry a DOCTYPE (XHTML, DocBook): use
  defusedxml, which forbids entity declarations but can allow a DTD.

**Example.**

```python
def no_dtd_text(document):
    parts = []
    def refuse_doctype(*_args):
        raise ValueError("DOCTYPE is not allowed")
    parser = xml.parsers.expat.ParserCreate()
    parser.StartDoctypeDeclHandler = refuse_doctype
    parser.CharacterDataHandler = parts.append
    parser.Parse(document, True)
    return "".join(parts)
```

**Cost removed.** Both the XXE document and the nested-entity document
raise `ValueError`; `<r>ok</r>` still parses to `ok`.

**Verify.**

1. `python3 assets/examples/python/test_parsers.py
   ExternalEntities.test_no_dtd_parser_rejects_doctype`

## Java disallow-doctype-decl

**Definition.** On a `DocumentBuilderFactory`, set
`http://apache.org/xml/features/disallow-doctype-decl` to `true` so any
DOCTYPE is a fatal error. OWASP recommends this feature for Java
(OWASP XXE cheat sheet). Fixes CWE-611 and CWE-776.

**Use when.**

- Java code creates `DocumentBuilderFactory`, `SAXParserFactory`,
  `XMLInputFactory`, `TransformerFactory`, or `SchemaFactory` for
  untrusted XML with default settings.

**Do not use when.**

- Documents need a DTD: set `ACCESS_EXTERNAL_DTD` and
  `ACCESS_EXTERNAL_SCHEMA` to `""`, turn off external entities, and test
  each factory separately.

**Example.** Runnable: `java assets/examples/java/Xxe.java
vulnerable|fixed SECRET_FILE` (single-file launch; no class files).

```java
DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
f.setFeature(
    "http://apache.org/xml/features/disallow-doctype-decl", true);
f.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
f.setXIncludeAware(false);
f.setExpandEntityReferences(false);
```

**Cost removed.** Local, OpenJDK 25.0.4.1: the default factory returned
the secret file's text; the fixed one printed `rejected: DOCTYPE is
disallowed`. A separate local run with only `FEATURE_SECURE_PROCESSING`
also refused the file ("'file' access is not allowed due to restriction
set by the accessExternalDTD property"), but OWASP notes that behavior
varies across implementations, so keep disallow-doctype-decl.

**Verify.**

1. `sh assets/examples/verify.sh local` runs both modes and greps the
   results.
1. `rg -n 'ParserFactory|XMLInputFactory' --type java` in the target;
   check each factory's features.

## Expat amplification limit

**Definition.** Expat 2.4.0 added billion-laughs protection
(CVE-2013-0340), which aborts a document whose entity expansion exceeds
an amplification factor; later releases extended it ([Expat
Changes][expat-changes]). The Python docs say Expat below 2.7.2 may be
vulnerable to billion laughs, quadratic blowup, and large tokens, and say
to check `pyexpat.EXPAT_VERSION` ([XML security][xml-sec]).
Covers CWE-776 for ElementTree, minidom, and SAX.

**Use when.**

- The service parses untrusted XML with the stdlib and runs on an
  interpreter whose Expat you do not control (system Python, old
  container images).

**Do not use when.**

- You need zero entity processing: use the DOCTYPE rejection above.
- The parser is `xmlrpc`: the docs list it as vulnerable to decompression
  bombs, which Expat does not limit.

**Example.**

```python
def laughs(levels=10):
    names = [f"e{i}" for i in range(levels)]
    decls = [f'<!ENTITY {names[0]} "lol">']
    for prev, name in itertools.pairwise(names):
        decls.append(f'<!ENTITY {name} "{("&" + prev + ";") * 10}">')
    body = "".join(decls)
    return f"<?xml version='1.0'?><!DOCTYPE r [{body}]><r>&{names[-1]};</r>"
```

**Cost removed.** Local, `expat_2.7.4`: `ET.fromstring(laughs())` raised
`ParseError: limit on input amplification factor (from DTD and entities)
breached` instead of expanding 10^9 `lol`s.

**Verify.**

1. `python3 -c 'import pyexpat; print(pyexpat.EXPAT_VERSION)'` on the
   deployed interpreter, not just locally.
1. `python3 assets/examples/python/test_parsers.py EntityExpansion`
   (skips below 2.7.2).

## defusedxml

**Definition.** `defusedxml` wraps the stdlib parsers and raises
`EntitiesForbidden` on entity declarations by default, and
`DTDForbidden` with `forbid_dtd=True`
([defusedxml][defusedxml]). OWASP's XXE cheat sheet recommends it for
Python.

**Use when.**

- The project can take a dependency and parses untrusted XML with
  `xml.etree`, `minidom`, `sax`, or `xmlrpc`.

**Do not use when.**

- lxml is the parser: the defusedxml README marks `defusedxml.lxml`
  deprecated; configure lxml's `XMLParser` options instead and test them
  with the documents above.

**Example.** Runnable: `assets/examples/thirdparty/defused_xml.py`.

```python
import defusedxml.ElementTree as DET

DET.fromstring(DOC)                  # raises EntitiesForbidden
DET.fromstring(DOC, forbid_dtd=True)  # raises DTDForbidden
DET.fromstring("<r>ok</r>").text     # "ok"
```

**Cost removed.** Local, defusedxml 0.7.1: the stdlib parsed the
internal entity to `expanded`; defusedxml refused it.

**Verify.**

1. `uv run --no-project --with defusedxml python
   assets/examples/thirdparty/defused_xml.py` prints `PASS`.

[pathlib-rel]:
https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to
[tar-filter]:
https://docs.python.org/3/library/tarfile.html#tarfile-extraction-filter
[os-access]: https://docs.python.org/3/library/os.html#os.access
[posix-open]:
https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html
[pickle]: https://docs.python.org/3/library/pickle.html#restricting-globals
[pyyaml]: https://github.com/yaml/pyyaml/blob/main/CHANGES
[sax]: https://docs.python.org/3/library/xml.sax.html
[sax-ges]:
https://docs.python.org/3/library/xml.sax.handler.html#xml.sax.handler.feature_external_ges
[owasp-xxe]:
https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html
[xml-sec]: https://docs.python.org/3/library/xml.html#xml-security
[defusedxml]: https://github.com/tiran/defusedxml
[expat-changes]:
https://github.com/libexpat/libexpat/blob/master/expat/Changes
