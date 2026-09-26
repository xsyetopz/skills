# Agent failure modes

Coding agents write locally plausible code fast and lose global intent,
scope, and evidence. Each card names one predictable failure that no other
card covers, the rule that prevents it, and the command that detects it in
a diff. Run the commands on `git diff <base>` before reporting a change.
The other agent failures have their own cards:

| Failure | Card |
| --- | --- |
| A new pattern, client, or dependency where the repository has one | [One obvious way](zen-of-python.md#there-should-be-one-obvious-way-to-do-it) |
| One name for two concepts, or two names for one | [One concept, one term](names-and-types.md#one-concept-one-term) |
| Interface, factory, or option with one user | [Simple is better than complex](zen-of-python.md#simple-is-better-than-complex) |
| Long generated function mixing purposes | [Phases](function-shape.md#phases-validate-prepare-execute) |
| Guessed units, API behavior, or formats | [Refuse the temptation to guess](zen-of-python.md#refuse-the-temptation-to-guess) |
| Comment explaining code that names could explain | [Comments](state-errors-comments.md#comments-that-state-why) |

## Contents

- Unrequested churn
- Treating passing tests as proof
- Copying a defect as a convention
- Review order

## Unrequested churn

**Definition.** Renaming unrelated identifiers, reformatting untouched code,
reordering declarations, or rewriting working logic in the same change.
Lines the change does touch follow the project's formatter. That is the
one checkable meaning this skill gives PEP 20's "Beautiful is better than
ugly"; other aesthetic judgments are not grounds for a change.

**Use when.** Always: limit the diff to the requested behavior, and run
the project's formatter (`gofmt`, `rustfmt`, `ruff format`, `prettier`,
`clang-format`) in check mode on the changed files.

**Do not use when.**

- The task is a refactor or format change: do only that, in its own
  change.
- The project has no formatter. Never add one, or reformat untouched
  files, inside an unrelated change.
- Layout is deliberate and marked, as in aligned tables under
  `// clang-format off` or `# fmt: skip`.

**Example.** A bug fix in `parse_header` that also renames `buf` to
`buffer` in six other functions and reorders imports. Not (abridged to one
of the six renamed functions):

```diff
diff --git a/headers.py b/headers.py
index 8cb7c17..541de61 100644
--- a/headers.py
+++ b/headers.py
@@ -1,11 +1,11 @@
-import sys
 import re
+import sys


-def parse_header(buf: bytes) -> tuple[str, str]:
-    name, _, value = buf.decode().partition(":")
-    return name, value
+def parse_header(buffer: bytes) -> tuple[str, str]:
+    name, _, value = buffer.decode().partition(":")
+    return name.strip(), value.strip()


-def read_line(buf: bytes) -> bytes:
-    return buf.split(b"\r\n", 1)[0]
+def read_line(buffer: bytes) -> bytes:
+    return buffer.split(b"\r\n", 1)[0]
```

Instead, only the fix:

```diff
diff --git a/headers.py b/headers.py
index 8cb7c17..df86675 100644
--- a/headers.py
+++ b/headers.py
@@ -4,7 +4,7 @@ import re

 def parse_header(buf: bytes) -> tuple[str, str]:
     name, _, value = buf.decode().partition(":")
-    return name, value
+    return name.strip(), value.strip()


 def read_line(buf: bytes) -> bytes:
```

A changed file that does not match the formatter shows up in its check
mode; `gofmt -d` on
[`unformatted/add.go.txt`][unformatted]:

```diff
 package unformatted
-func  Add(a int,b int) int{
-return a+b}
+
+func Add(a int, b int) int {
+    return a + b
+}
```

gofmt indents with a tab; the listing shows it as four spaces.

**Cost removed.** Review effort, merge conflicts, and arguments about
layout; unrelated lines hide the real change. `gofmt -l` lists the
unformatted fixture and no example file. `gofmt -l` exits 0 either way, so
the check must test for empty output.

**Verify.**

1. `git diff --stat <base>` touches only files the task needs.
1. The project's check mode passes on the changed files:
   `ruff format --check`, `cargo fmt --check`, `test -z "$(gofmt -l .)"`,
   `prettier --check`.
1. `git diff -w --stat <base>` versus `git diff --stat <base>`: a large
   difference means whitespace-only churn.
1. Every hunk in `git diff <base>` maps to the requested behavior.

## Treating passing tests as proof

**Definition.** Claiming correctness because the suite is green when no
test exercises the changed invariant, boundary, error path, concurrency, or
resource lifetime.

**Use when.** Before claiming a change is done.

**Do not use when.** No exception: never skip it.

**Example.** `candidate_load_port` now raises on bad JSON, but the only
test covers a valid file, so the green suite proves nothing about the
change. The only test:

```python
class LoadPortTest(unittest.TestCase):
    def test_reads_port(self) -> None:
        port = se.candidate_load_port(lambda _: '{"port": 9000}', "c.json")
        self.assertEqual(port, 9000)
```

With a test for the changed behavior, which fails against
`baseline_load_port` from `assets/examples/readable/python/state_errors.py`:

```python
class LoadPortTest(unittest.TestCase):
    def test_reads_port(self) -> None:
        port = se.candidate_load_port(lambda _: '{"port": 9000}', "c.json")
        self.assertEqual(port, 9000)

    def test_bad_json_raises_config_error(self) -> None:
        with self.assertRaises(se.ConfigError):
            se.candidate_load_port(lambda _: "{not json", "c.json")
```

**Cost removed.** False confidence.

**Verify.**

1. Temporarily revert the behavior change; at least one test must fail.
1. List the boundary and error cases the change affects and point to the
   test for each.

## Copying a defect as a convention

**Definition.** Repeating a suspicious pattern because nearby code does it
(swallowed exceptions, missing bounds checks, string-built SQL).

**Use when.** Imitating neighboring code.

**Do not use when.** The pattern is a deliberate, documented workaround:
follow it and keep its comment.

**Example.** Every handler in a module does `except Exception: pass`. Do
not add another: handle the specific error in the new code and report the
existing pattern as a follow-up.

Not:

```python
def load_settings(path: str) -> dict[str, object]:
    try:
        return read_settings(path)
    except Exception:
        pass
```

Instead:

```python
def load_settings(path: str) -> dict[str, object]:
    try:
        return read_settings(path)
    except FileNotFoundError:
        return dict(DEFAULT_SETTINGS)
```

**Cost removed.** One more copy of a defect.

**Verify.**

1. For a copied pattern, find its origin (`git log -S 'pattern' --oneline`)
   and any issue or comment that justifies it; without one, do not copy
   it.

## Review order

**Definition.** Review a change in this order and stop at the first level
that fails:

1. Is the behavior correct?
1. Are the invariants preserved?
1. Is the architecture still coherent?
1. Is the control flow obvious?
1. Are names and terminology correct?
1. Are state and side effects explicit?
1. Is the abstraction level consistent?
1. Is the working-memory burden reasonable (metrics)?
1. Is the diff as narrow as it can be?
1. Only then: style details the formatter does not handle.

**Use when.** Reviewing your own diff before reporting, or someone else's.

**Do not use when.** No exception: never approve confusing code because it
is well formatted.

**Example.** A diff reformats a file and changes a comparison from `<` to
`<=`. Review the comparison (behavior) first, not the formatting.

```diff
diff --git a/quota.py b/quota.py
index be84cdb..5811fbe 100644
--- a/quota.py
+++ b/quota.py
@@ -1,6 +1,6 @@
-def within_quota(used:int,limit:int)->bool:
-    return used<limit
+def within_quota(used: int, limit: int) -> bool:
+    return used <= limit


-def remaining(used:int,limit:int)->int:
-    return max(limit-used,0)
+def remaining(used: int, limit: int) -> int:
+    return max(limit - used, 0)
```

The review notes, highest level first:

```text
1. Behavior: within_quota(5, 5) was False and is now True (< became <=).
   Is the boundary change intended, and which test covers used == limit?
10. Style: the other lines are formatter spacing; no finding.
```

**Cost removed.** Style discussions hiding behavior bugs.

**Verify.**

1. The review notes list findings grouped by these levels, highest first.

[unformatted]: ../assets/examples/zen-of-python/langs/go/unformatted/add.go.txt
