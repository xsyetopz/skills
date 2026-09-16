# Construct examples that demonstrate the claimed behavior

Use a stated contract, actual implementations, independent observations, and
runnable commands. Label an example by its defect or correction. Reserve
red/green for the observed results of executing a test, not design preference.

## One operation does not automatically need a registry

Example contract: move a supplied file to an absent sibling path, preserving its
bytes, removing the source name, and returning the destination. This fixture
assumes a caller-owned temporary directory and no concurrent path mutation. It
does not promise cross-device atomicity or a race-free no-clobber primitive.

A factory and registry for this single operation would not add required
behavior. Returning `(old, new)` would not perform the operation at all. The
actual [implementation](../assets/rename-contract/rename_operation.py) uses
`Path.rename`; the [tests](../assets/rename-contract/test_rename_operation.py)
observe both names and bytes. They accept an equivalent `os.rename` variant and
reject a no-op returning the destination. Missing-source and existing-target
checks establish the fixture's specific failure contract.

Run from the skill root:

```sh
python3 assets/rename-contract/test_rename_operation.py
```

The fixture is not a mandated rename API for another project. Inspect the actual
filesystem, concurrency, overwrite, and portability requirements before adapting
it. Add a class or interface only when an evidenced boundary needs one.

## Structured data needs an existing or standard format

Example contract: two components exchange an identifier and arbitrary text that
may contain `|`; no existing wire protocol constrains this illustrative format.

The defective delimiter scheme cannot recover the fields:

```python
message = "42|start|stop"
message_id, text = message.split("|")
```

JSON expresses the same data without inventing delimiter escaping:

```python
import json

message = {"id": 42, "text": "start|stop"}
wire = json.dumps(message)
assert json.loads(wire) == {"id": 42, "text": "start|stop"}
```

Run the snippets separately. The delimiter case should fail with unpacking
`ValueError`; JSON should preserve the stated fields. A process exit alone does
not establish the failure cause. Do not replace a real established protocol
merely because this example uses JSON.

## A directory layout is not a runnable reproduction

A list such as `repro.py`, `fixture.json`, and a setup note is an illustration,
not evidence that those files exist or reproduce a defect. Deliver the actual
required files and exact command, input, expected observation, and relevant
versions. Run them from an isolated location without undeclared caches or local
paths. A prose claim that the implementation works cannot substitute for the
implementation, and a generic nonzero exit cannot identify the original defect.

Keep reproduction scope minimal. A compiler-only failure may need one source
file and one compiler command, not a project generator or CI pipeline. If a
private input cannot be supplied, state the remaining reproducibility limit.
