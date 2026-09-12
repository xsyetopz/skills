# Pair construction examples

Use this shape. Replace only the condition-specific details; do not add a
pattern name as justification.

```markdown
**Deciding condition:** <literal condition that makes GREEN required>.

### RED — DO NOT: <specific defect>
<same-context wrong code>

Why RED:
- <violated invariant and consequence>

### GREEN — DO: <corresponding correction>
<same-context correct code>

Why GREEN:
- <condition is met with no unneeded structure>

Check: <exact command, assertion, or inspection>
```

## One implementation does not justify a registry

**Deciding condition:** The CLI has one current `rename` operation, no plugin
boundary, no alternate implementation, and no requested extension point.

### RED — DO NOT: add a factory and registry for one function

```python
class RenameCommand:
    def run(self, old: str, new: str) -> tuple[str, str]:
        return old, new

COMMANDS = {"rename": RenameCommand()}


def execute(name: str, old: str, new: str) -> tuple[str, str]:
    return COMMANDS[name].run(old, new)
```

Why RED:

- The registry and class represent no present boundary or alternative.
- Callers must navigate extra indirection to invoke the only operation.

### GREEN — DO: call the one operation directly

```python
def rename(old: str, new: str) -> tuple[str, str]:
    return old, new


assert rename("draft.txt", "final.txt") == ("draft.txt", "final.txt")
```

Why GREEN:

- It supplies the requested operation without inventing an extension layer.
- A future plugin contract can be introduced when a real plugin boundary exists.

Check: run `python3 green.py`; inspect the request for a current alternate
implementation, platform contract, test seam, or extension point before adding
an abstraction.

## Structured data needs a standard format

**Deciding condition:** Two independently maintained components exchange text
that can contain the delimiter, and no existing protocol constrains the format.

### RED — DO NOT: invent a delimiter protocol

```python
message = "42|start|stop"
message_id, text = message.split("|")
```

Why RED:

- The payload value contains the delimiter, so decoding raises `ValueError`.
- A custom format adds escaping and compatibility rules without need.

### GREEN — DO: use the standard-library JSON format

```python
import json

message = {"id": 42, "text": "start|stop"}
wire = json.dumps(message)
assert json.loads(wire) == message
```

Why GREEN:

- JSON preserves the same data without a custom escaping rule.
- The standard library provides the serializer and parser.

Check: run the RED snippet as `python3 red.py` and confirm it exits nonzero;
run the GREEN snippet as `python3 green.py` and confirm it exits zero.

## A report fragment is not an MRE

**Deciding condition:** A maintainer must reproduce an observed runtime failure
without access to the reporter's private repository.

### RED — DO NOT: provide only a call site

```text
client.fetch_data()
# It crashes sometimes.
```

Why RED:

- The command, versions, input, exact diagnostic, and required files are absent.
- A maintainer cannot independently verify the claimed failure.

### GREEN — DO: provide the complete executable artifact

```text
repro/
├── pyproject.toml
├── repro.py
├── fixture.json
└── README.md  # prerequisites, exact command, expected and actual result
```

Why GREEN:

- The maintainer receives every required file and exact execution instructions.
- The observed result can be checked without reconstructing private context.

Check: copy `repro/` to a clean directory and run the command in its
`README.md`.
